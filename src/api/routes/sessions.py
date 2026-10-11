from fastapi import APIRouter
from src.app import session_repo, message_repo
from uuid import UUID
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/sessions")
def create_session():

    session = session_repo.create(
        title="New conversation"
    )

    return session


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: UUID):

    session = session_repo.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    messages = message_repo.list_by_session(
        session_id
    )

    return {
        "session_id": session_id,
        "messages": messages
    }