import re


FORBIDDEN_OPERATIONS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
}


def validate_sql(query: str) -> tuple[bool, str]:

    cleaned_query = query.strip()

    if not cleaned_query:
        return False, "SQL query is empty."

    upper_query = cleaned_query.upper()

    # Only SELECT / WITH queries
    if not (
        upper_query.startswith("SELECT")
        or upper_query.startswith("WITH")
    ):
        return False, "Only read-only SELECT queries are allowed."

    # Block multiple statements
    statements = [
        statement.strip()
        for statement in cleaned_query.split(";")
        if statement.strip()
    ]

    if len(statements) > 1:
        return False, "Multiple SQL statements are not allowed."

    # Forbidden operations
    for operation in FORBIDDEN_OPERATIONS:
        if re.search(
            rf"\b{operation}\b",
            upper_query
        ):
            return False, f"{operation} operations are forbidden."

    return True, ""