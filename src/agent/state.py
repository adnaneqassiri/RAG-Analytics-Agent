import operator
from typing import Annotated, Sequence, TypedDict, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Main history
    messages: Annotated[list[BaseMessage], add_messages]

    # User input
    question: str

    # Candidate answer produced by agent
    candidate_answer: NotRequired[str]

    sql_history: Annotated[
        list[dict],
        operator.add
    ]
    
    # Reflection
    reflection: NotRequired[str | None]
    approved: NotRequired[bool]

    # Control
    iterations: int