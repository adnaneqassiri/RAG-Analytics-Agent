from pydantic import BaseModel


class QueryRequest(BaseModel):
    message: str