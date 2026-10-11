from src.agent.state import AgentState
from src.llm import llm
from pydantic import BaseModel, Field
from src.agent.prompts.reflection import reflection_prompt

class ReflectionOutput(BaseModel):
    approved: bool = Field(description="True if the current analysis fully answers the user's question using sufficient evidence.")
    feedback: str = Field(description="If rejected, explain precisely what is missing or incorrect. If approved, briefly explain why.")

reflection_llm = llm.with_structured_output(ReflectionOutput)

def reflection_node(state: AgentState) -> AgentState:
    prompt= f"""
        {reflection_prompt}
        
        USER QUESTION:
        {state["question"]}

        EXECUTED SQL QUERIES HISTORY:
        {state.get("sql_history", [])}
        
        CANDIDATE ANSWER:
        {state.get("candidate_answer", "")}
    """
    result = reflection_llm.invoke(prompt)
    print(result)
    return {
        "approved": result.approved,
        "reflection": result.feedback
    }
