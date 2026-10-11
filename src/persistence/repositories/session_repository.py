from uuid import uuid4


class SessionRepository:

    def __init__(self, connection_factory):
        self.connection_factory = connection_factory

    def create(self, title: str | None = None) -> dict:
        session_id = uuid4()

        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app.sessions (
                        id,
                        title
                    )
                    VALUES (%s, %s)
                    RETURNING id, title, created_at, updated_at
                    """,
                    (session_id, title)
                )

                row = cur.fetchone()

        return {
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
    
    def get(self, session_id) -> dict | None:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM app.sessions
                    WHERE id = %s
                    """,
                    (session_id,)
                )

                row = cur.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
    
    def list_all(self) -> list[dict]:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM app.sessions
                    ORDER BY updated_at DESC
                    """
                )

                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
            for row in rows
        ]
    
    def touch(self, session_id) -> None:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app.sessions
                    SET updated_at = NOW()
                    WHERE id = %s
                    """,
                    (session_id,)
                )
    
    def delete(self, session_id) -> None:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM app.sessions
                    WHERE id = %s
                    """,
                    (session_id,)
                )