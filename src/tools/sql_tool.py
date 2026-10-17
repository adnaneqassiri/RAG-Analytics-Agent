import json

from langchain_core.tools import tool

from src.database.executor import SQLExecutor
from src.results.manager import ResultsManager


def create_sql_tool(
    executor: SQLExecutor,
    results_manager: ResultsManager,
):

    @tool
    def execute_sql(query: str) -> str:
        """
        Execute a read-only PostgreSQL query.

        Successful query results are stored temporarily.

        Returns a result_id, metadata, and a small preview.
        The full result is not placed in the LLM context.
        """

        try:
            result = executor.execute(query)

        except Exception as exc:
            return json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                }
            )

        # Only successful SQL reaches this point.
        stored_result = results_manager.save(
            columns=result["columns"],
            rows=result["rows"],
        )

        preview_size = 5

        preview = [
            dict(
                zip(
                    result["columns"],
                    row,
                )
            )
            for row in result["rows"][:preview_size]
        ]

        response = {
            "status": "success",
            "result_id": stored_result.result_id,
            "columns": stored_result.columns,
            "row_count": stored_result.row_count,
            "truncated": result.get(
                "truncated",
                False,
            ),
            "preview": preview,
        }

        return json.dumps(
            response,
            default=str,
        )

    return execute_sql