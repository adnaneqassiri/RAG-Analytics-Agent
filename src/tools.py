from langchain_core.tools import tool
import pandas as pd
import psycopg
from dotenv import load_dotenv
import re
import os



load_dotenv()
db_url = os.getenv("DB_URL")
MAX_ROWS = 500


FORBIDDEN_SQL = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|"
    r"CREATE|GRANT|REVOKE|COPY|CALL"
    r")\b",
    re.IGNORECASE
)


def validate_sql(sql: str) -> tuple[bool, str]:
    sql = sql.strip()

    if not sql:
        return False, "SQL query is empty."

    # Only allow read queries
    if not re.match(
        r"^(SELECT|WITH)\b",
        sql,
        re.IGNORECASE
    ):
        return False, "Only SELECT/read-only queries are allowed."

    # Block dangerous statements
    if FORBIDDEN_SQL.search(sql):
        return False, "Forbidden SQL operation detected."

    # Only one statement
    without_final_semicolon = sql.rstrip(";")

    if ";" in without_final_semicolon:
        return False, "Multiple SQL statements are not allowed."

    return True, ""

DB_SCHEMA = """
DATABASE: PostgreSQL e-commerce database

TABLE customers
- customer_id INTEGER PRIMARY KEY
- name VARCHAR
- region VARCHAR
- created_at TIMESTAMP

TABLE products
- product_id INTEGER PRIMARY KEY
- name VARCHAR
- category VARCHAR
- price NUMERIC

TABLE orders
- order_id INTEGER PRIMARY KEY
- customer_id INTEGER FOREIGN KEY REFERENCES customers(customer_id)
- order_date TIMESTAMP
- status VARCHAR
  Possible values: completed, cancelled, pending

TABLE order_items
- order_item_id INTEGER PRIMARY KEY
- order_id INTEGER FOREIGN KEY REFERENCES orders(order_id)
- product_id INTEGER FOREIGN KEY REFERENCES products(product_id)
- quantity INTEGER
- unit_price NUMERIC

TABLE payments
- payment_id INTEGER PRIMARY KEY
- order_id INTEGER FOREIGN KEY REFERENCES orders(order_id)
- amount NUMERIC
- payment_method VARCHAR
- payment_date TIMESTAMP

RELATIONSHIPS
- customers.customer_id = orders.customer_id
- orders.order_id = order_items.order_id
- products.product_id = order_items.product_id
- orders.order_id = payments.order_id
"""



@tool
def get_db_context():
    """Function to retrieve the db context, db schema, KPIs, database structure"""
    return DB_SCHEMA






@tool
def execute_sql(query: str) -> str:
    """
    Execute a safe, read-only SQL query against the analytics database.
    Returns the query result or an error message.
    please pass in 'query' for the sql query
    """

    safe, reason = validate_sql(query)

    if not safe:
        return f"SQL_BLOCKED: {reason}"

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:

                # Database-level read-only protection
                cur.execute(
                    "SET TRANSACTION READ ONLY"
                )

                # Prevent very expensive queries
                cur.execute(
                    "SET LOCAL statement_timeout = '3000ms'"
                )

                # Execute model-generated query
                cur.execute(query)

                rows = cur.fetchmany(MAX_ROWS + 1)

                columns = [
                    desc.name
                    for desc in cur.description
                ]

        # Result-size guardrail
        if len(rows) > MAX_ROWS:
            return (
                "SQL_RESULT_TOO_LARGE: "
                f"More than {MAX_ROWS} rows were returned. "
                "Use filtering, aggregation, or LIMIT."
            )

        df = pd.DataFrame(
            rows,
            columns=columns
        )

        return df.to_string(index=False)

    except psycopg.Error as e:
        return (
            "SQL_ERROR: "
            f"{type(e).__name__}: {e}"
        )



tools = [execute_sql, get_db_context]