from __future__ import annotations

import json
import os
import re
import uuid

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence


RESULT_ID_PATTERN = re.compile(r"^res_[0-9a-f]{32}$")


class ResultManagerError(Exception):
    """Base exception for result storage errors."""


class ResultNotFoundError(ResultManagerError):
    """Raised when a result does not exist."""


class ResultExpiredError(ResultManagerError):
    """Raised when a result has expired."""


class InvalidResultIdError(ResultManagerError):
    """Raised when a result ID has an invalid format."""


class ResultAccessDeniedError(ResultManagerError):
    """Raised when a result belongs to another session."""


@dataclass(frozen=True)
class StoredResultRef:
    result_id: str
    columns: list[str]
    row_count: int
    created_at: str
    expires_at: str


class ResultsManager:
    """
    Temporary storage for SQL query results.

    SQL results are stored outside the LangGraph message state.
    The agent receives only:
        - result_id
        - columns
        - row_count
        - small preview

    Later, the visualization sandbox can load the full result
    by using result_id.
    """

    def __init__(
        self,
        base_dir: str | Path = ".runtime/results",
        ttl_seconds: int = 600,
    ):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than 0")

        self.base_dir = Path(base_dir)
        self.ttl_seconds = ttl_seconds

        self.base_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def save(
        self,
        *,
        columns: Sequence[str],
        rows: Sequence[Sequence[Any]],
        session_id: str | None = None,
        run_id: str | None = None,
    ) -> StoredResultRef:
        """
        Save a SQL result and return an opaque result reference.

        session_id and run_id are optional for now, but are included
        because later we will use them for isolation and cleanup.
        """

        self.cleanup_expired()

        result_id = f"res_{uuid.uuid4().hex}"

        created_at_dt = datetime.now(timezone.utc)
        expires_at_dt = created_at_dt + timedelta(
            seconds=self.ttl_seconds
        )

        normalized_columns = [str(column) for column in columns]

        payload = {
            "result_id": result_id,
            "session_id": session_id,
            "run_id": run_id,
            "columns": normalized_columns,
            "row_count": len(rows),
            "rows": [list(row) for row in rows],
            "created_at": created_at_dt.isoformat(),
            "expires_at": expires_at_dt.isoformat(),
        }

        final_path = self._path_for(result_id)

        # Temporary file + os.replace gives us an atomic write.
        temporary_path = final_path.with_suffix(".tmp")

        try:
            with temporary_path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    payload,
                    file,
                    ensure_ascii=False,
                    default=self._json_default,
                )

            os.replace(
                temporary_path,
                final_path,
            )

        finally:
            if temporary_path.exists():
                temporary_path.unlink(missing_ok=True)

        return StoredResultRef(
            result_id=result_id,
            columns=normalized_columns,
            row_count=len(rows),
            created_at=created_at_dt.isoformat(),
            expires_at=expires_at_dt.isoformat(),
        )

    def load(
        self,
        result_id: str,
        *,
        expected_session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Load a stored SQL result.

        Later create_visualization() will use this method.
        """

        path = self._path_for(result_id)

        if not path.exists():
            raise ResultNotFoundError(
                f"Result '{result_id}' does not exist."
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        if self._is_expired(payload):
            self.delete(result_id)

            raise ResultExpiredError(
                f"Result '{result_id}' has expired."
            )

        if expected_session_id is not None:
            stored_session_id = payload.get("session_id")

            if stored_session_id != expected_session_id:
                raise ResultAccessDeniedError(
                    "Result does not belong to this session."
                )

        return payload

    def delete(
        self,
        result_id: str,
    ) -> None:
        """Delete one stored result."""

        path = self._path_for(result_id)
        path.unlink(missing_ok=True)

    def cleanup_expired(self) -> int:
        """
        Remove expired temporary results.

        Returns the number of deleted files.
        """

        deleted = 0

        for path in self.base_dir.glob("res_*.json"):
            try:
                with path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    payload = json.load(file)

                if self._is_expired(payload):
                    path.unlink(missing_ok=True)
                    deleted += 1

            except (json.JSONDecodeError, OSError):
                # Temporary result storage is disposable.
                # Corrupted files should not remain forever.
                path.unlink(missing_ok=True)
                deleted += 1

        return deleted

    def cleanup_run(
        self,
        run_id: str,
    ) -> int:
        """
        Delete all results created during one agent run.

        We will use this later once run_id is wired into
        AgentService / LangGraph execution.
        """

        deleted = 0

        for path in self.base_dir.glob("res_*.json"):
            try:
                with path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    payload = json.load(file)

                if payload.get("run_id") == run_id:
                    path.unlink(missing_ok=True)
                    deleted += 1

            except (json.JSONDecodeError, OSError):
                continue

        return deleted

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _path_for(
        self,
        result_id: str,
    ) -> Path:
        if not RESULT_ID_PATTERN.fullmatch(result_id):
            raise InvalidResultIdError(
                f"Invalid result ID: {result_id}"
            )

        return self.base_dir / f"{result_id}.json"

    @staticmethod
    def _is_expired(
        payload: dict[str, Any],
    ) -> bool:
        expires_at = payload.get("expires_at")

        if not expires_at:
            return True

        try:
            expiration = datetime.fromisoformat(expires_at)

        except ValueError:
            return True

        return datetime.now(timezone.utc) >= expiration

    @staticmethod
    def _json_default(value: Any):
        """
        Convert common PostgreSQL/Python values to JSON-safe values.
        """

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, bytes):
            return value.decode(
                "utf-8",
                errors="replace",
            )

        return str(value)