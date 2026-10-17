from __future__ import annotations

import json
import mimetypes
import os
import tempfile
import uuid

from dataclasses import dataclass
from pathlib import Path

import docker
import requests
from docker.errors import DockerException


class SandboxError(Exception):
    """Base exception for sandbox failures."""


class SandboxExecutionError(SandboxError):
    """Raised when Python execution fails."""


class SandboxTimeoutError(SandboxError):
    """Raised when sandbox execution exceeds the timeout."""


@dataclass(frozen=True)
class SandboxArtifact:
    name: str
    path: Path
    mime_type: str | None


@dataclass(frozen=True)
class SandboxResult:
    run_id: str
    stdout: str
    artifacts: list[SandboxArtifact]


class PythonSandboxRunner:
    """
    Execute agent-generated Python inside an isolated Docker container.

    The container receives only:
        /input/result.json   -> read only
        /code/main.py        -> read only
        /output/             -> writable

    The generated Python gets these predefined objects:
        df   -> pandas DataFrame containing the SQL result
        pd   -> pandas
        np   -> numpy
        plt  -> matplotlib.pyplot
        sns  -> seaborn
    """

    def __init__(
        self,
        image: str = "analytics-python-sandbox:latest",
        output_dir: str | Path = ".runtime/python_runs",
        timeout_seconds: int = 15,
        memory_limit: str = "512m",
        cpu_count: float = 1.0,
        max_artifacts: int = 10,
    ):
        self.image = image
        self.output_dir = Path(output_dir)
        self.timeout_seconds = timeout_seconds
        self.memory_limit = memory_limit
        self.cpu_count = cpu_count
        self.max_artifacts = max_artifacts

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            self.client = docker.from_env()
            self.client.ping()

        except DockerException as exc:
            raise SandboxError(
                "Docker is not available. "
                "Make sure the Docker daemon is running."
            ) from exc

    def run(
        self,
        *,
        columns: list[str],
        rows: list[list],
        code: str,
    ) -> SandboxResult:
        """
        Execute Python against one SQL result.

        `columns` and `rows` come from ResultsManager.
        """

        run_id = f"run_{uuid.uuid4().hex}"

        run_dir = self.output_dir / run_id
        artifact_dir = run_dir / "artifacts"

        artifact_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        container = None

        with tempfile.TemporaryDirectory(
            prefix="analytics_python_"
        ) as temp_directory:

            temp_path = Path(temp_directory)

            input_dir = temp_path / "input"
            code_dir = temp_path / "code"

            input_dir.mkdir()
            code_dir.mkdir()

            self._write_input(
                input_dir=input_dir,
                columns=columns,
                rows=rows,
            )

            self._write_program(
                code_dir=code_dir,
                code=code,
            )

            try:
                container_user = (
                    f"{os.getuid()}:{os.getgid()}"
                )
            except AttributeError:
                container_user = "1000:1000"

            nano_cpus = int(
                self.cpu_count * 1_000_000_000
            )

            try:
                container = self.client.containers.run(
                    image=self.image,

                    command=[
                        "python",
                        "/code/main.py",
                    ],

                    detach=True,

                    # No internet / external networking.
                    network_disabled=True,

                    # Resource limits.
                    mem_limit=self.memory_limit,
                    nano_cpus=nano_cpus,
                    pids_limit=64,

                    # Container filesystem is immutable.
                    read_only=True,

                    # Remove Linux capabilities.
                    cap_drop=["ALL"],

                    security_opt=[
                        "no-new-privileges:true"
                    ],

                    user=container_user,

                    environment={
                        "HOME": "/tmp",
                        "MPLBACKEND": "Agg",
                        "MPLCONFIGDIR": "/tmp/matplotlib",
                    },

                    # Python/matplotlib can write temporary files
                    # here, but they disappear with the container.
                    tmpfs={
                        "/tmp": (
                            "rw,noexec,nosuid,"
                            "size=128m"
                        )
                    },

                    volumes={
                        str(input_dir.resolve()): {
                            "bind": "/input",
                            "mode": "ro",
                        },
                        str(code_dir.resolve()): {
                            "bind": "/code",
                            "mode": "ro",
                        },
                        str(artifact_dir.resolve()): {
                            "bind": "/output",
                            "mode": "rw",
                        },
                    },
                )

                try:
                    result = container.wait(
                        timeout=self.timeout_seconds
                    )

                except requests.exceptions.ReadTimeout:
                    container.kill()

                    raise SandboxTimeoutError(
                        "Python execution exceeded "
                        f"{self.timeout_seconds} seconds."
                    )

                stdout = container.logs(
                    stdout=True,
                    stderr=True,
                ).decode(
                    "utf-8",
                    errors="replace",
                )

                status_code = result.get(
                    "StatusCode",
                    1,
                )

                if status_code != 0:
                    raise SandboxExecutionError(
                        "Python execution failed:\n"
                        f"{stdout}"
                    )

                artifacts = self._collect_artifacts(
                    artifact_dir
                )

                return SandboxResult(
                    run_id=run_id,
                    stdout=stdout,
                    artifacts=artifacts,
                )

            except DockerException as exc:
                raise SandboxError(
                    f"Docker sandbox failure: {exc}"
                ) from exc

            finally:
                if container is not None:
                    try:
                        container.remove(
                            force=True
                        )
                    except DockerException:
                        pass

    # --------------------------------------------------
    # Input
    # --------------------------------------------------

    @staticmethod
    def _write_input(
        *,
        input_dir: Path,
        columns: list[str],
        rows: list[list],
    ) -> None:

        payload = {
            "columns": columns,
            "rows": rows,
        }

        path = input_dir / "result.json"

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                default=str,
            )

    # --------------------------------------------------
    # Trusted program wrapper
    # --------------------------------------------------

    @staticmethod
    def _write_program(
        *,
        code_dir: Path,
        code: str,
    ) -> None:

        program = f"""
import json

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================
# TRUSTED DATA LOADING
# ==========================================

with open(
    "/input/result.json",
    "r",
    encoding="utf-8"
) as file:
    _payload = json.load(file)


df = pd.DataFrame(
    _payload["rows"],
    columns=_payload["columns"],
)


# ==========================================
# AGENT GENERATED CODE
# ==========================================

{code}


# ==========================================
# TRUSTED FIGURE CAPTURE
# ==========================================

# If Python created matplotlib figures but did not
# explicitly save anything, save them automatically.

from pathlib import Path

_output_dir = Path("/output")

_existing_files = list(
    _output_dir.iterdir()
)

if not _existing_files:
    _figure_numbers = plt.get_fignums()

    for _index, _figure_number in enumerate(
        _figure_numbers,
        start=1,
    ):
        _figure = plt.figure(
            _figure_number
        )

        _figure.tight_layout()

        _figure.savefig(
            _output_dir
            / f"figure_{{_index}}.png",
            dpi=150,
            bbox_inches="tight",
        )
"""

        path = code_dir / "main.py"

        path.write_text(
            program,
            encoding="utf-8",
        )

    # --------------------------------------------------
    # Outputs
    # --------------------------------------------------

    def _collect_artifacts(
        self,
        artifact_dir: Path,
    ) -> list[SandboxArtifact]:

        artifacts: list[SandboxArtifact] = []

        for path in sorted(
            artifact_dir.iterdir()
        ):
            if not path.is_file():
                continue

            mime_type, _ = mimetypes.guess_type(
                path.name
            )

            artifacts.append(
                SandboxArtifact(
                    name=path.name,
                    path=path,
                    mime_type=mime_type,
                )
            )

            if len(artifacts) >= self.max_artifacts:
                break

        return artifacts