from fastapi import APIRouter

from src.api.schemas.requests import QueryRequest
from src.api.schemas.responses import QueryResponse
from src.app import agent_service

router = APIRouter()


from uuid import UUID

@router.post(
    "/sessions/{session_id}/messages",
    response_model=QueryResponse
)
def query_agent(
    session_id: UUID,
    request: QueryRequest
):

    result = agent_service.run(
        question=request.message,
        session_id=session_id
    )

    return QueryResponse(
        answer=result["answer"],
        sql_history=result.get("sql_history", [])
    )