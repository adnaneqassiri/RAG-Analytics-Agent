import psycopg

from src.database.guardrails import validate_sql


class SQLExecutor:
    def __init__(
        self,
        db_url: str,
        timeout_ms: int = 3000,
        max_rows: int = 500,
    ):
        self.db_url = db_url
        self.timeout_ms = timeout_ms
        self.max_rows = max_rows

    def execute(self, query: str) -> dict:
        # 1. Validate before touching PostgreSQL
        valid, reason = validate_sql(query)

        if not valid:
            raise ValueError(
                f"Query rejected by SQL guardrails: {reason}"
            )

        # 2. Execute inside a read-only transaction
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SET TRANSACTION READ ONLY"
                )

                cur.execute(
                    f"SET LOCAL statement_timeout = {int(self.timeout_ms)}"
                )

                cur.execute(query)

                columns = [
                    description.name
                    for description in cur.description
                ]

                # Fetch one extra row to detect truncation
                rows = cur.fetchmany(
                    self.max_rows + 1
                )

                truncated = (
                    len(rows) > self.max_rows
                )

                rows = rows[: self.max_rows]

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }