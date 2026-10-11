from src.database.connection import get_connection
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


    def execute(self, query: str):

        valid, reason = validate_sql(query)

        if not valid:
            return {
                "success": False,
                "error": reason,
            }

        try:

            with get_connection(self.db_url) as conn:

                with conn.cursor() as cursor:

                    cursor.execute(
                        "SET TRANSACTION READ ONLY"
                    )

                    cursor.execute(
                        f"SET LOCAL statement_timeout = {self.timeout_ms}"
                    )

                    cursor.execute(query)

                    rows = cursor.fetchmany(
                        self.max_rows
                    )

                    columns = [
                        description.name
                        for description in cursor.description
                    ]

                    data = [
                        dict(zip(columns, row))
                        for row in rows
                    ]

                    return {
                        "success": True,
                        "data": data,
                    }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }