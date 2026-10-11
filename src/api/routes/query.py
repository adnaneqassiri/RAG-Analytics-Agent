from fastapi import APIRouter

from src.api.schemas.requests import QueryRequest
from src.api.schemas.responses import QueryResponse
from src.app import agent_service

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse
)
def query_agent(request: QueryRequest):

    result = agent_service.run(
        question=request.message, session_id=''
    )
    answer = result["candidate_answer"]
    sql_history = result['sql_history']

    return QueryResponse(
        answer=answer,
        sql_history= sql_history
    )