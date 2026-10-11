import psycopg


def get_connection(db_url: str):
    return psycopg.connect(db_url)