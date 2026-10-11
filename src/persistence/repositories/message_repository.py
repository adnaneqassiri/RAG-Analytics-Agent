from uuid import uuid4

class MessageRepository:

    def __init__(self, connection_factory):
        self.connection_factory = connection_factory


    def create(
        self,
        session_id,
        role: str,
        content: str
    ):
        message_id = uuid4()

        with self.connection_factory() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO app.messages (
                        id,
                        session_id,
                        role,
                        content
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        message_id,
                        session_id,
                        role,
                        content
                    )
                )

        return message_id
    
    
    def list_by_session(self, session_id):

        with self.connection_factory() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT role, content
                    FROM app.messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    """,
                    (session_id,)
                )

                rows = cur.fetchall()

        return [
            {
                "role": row[0],
                "content": row[1]
            }
            for row in rows
        ]