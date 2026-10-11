from pydantic import BaseModel
from typing import Any


class QueryResponse(BaseModel):
    answer: str
    sql_history: list[dict[str, Any]]