import psycopg


def create_connection_factory(db_url: str):

    def get_connection():
        return psycopg.connect(db_url)

    return get_connection