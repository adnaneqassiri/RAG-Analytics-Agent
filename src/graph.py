from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage,  ToolMessage
from src.agent.state import AgentState
from src.tools import tools
from src.llm import llm
from src.tools import get_db_context, execute_sql
from pydantic import BaseModel, Field


class ReflectionOutput(BaseModel):

    approved: bool = Field(
        description="True if the current analysis fully answers the user's question using sufficient evidence."
    )

    feedback: str = Field(
        description="If rejected, explain precisely what is missing or incorrect. If approved, briefly explain why."
    )

llm_with_tools = llm.bind_tools(tools)
reflection_llm = llm.with_structured_output(ReflectionOutput)

SYSTEM_PROMPT = """
You are an autonomous data analytics agent.

Your goal is to answer the user's analytical question accurately using
the available tools.

You can:
- inspect database context and schema,
- execute safe read-only SQL queries,
- create visualizations when useful.

Rules:
0. Do not use table names or column names that doesnt exist in the retrieved db context.
1. Do not invent data.
2. Use tools whenever information from the database is required.
3. After receiving a tool result, evaluate whether you have enough
   information to answer the original question.
4. If the result is insufficient, call another appropriate tool.
5. Do not use Python if SQL alone can answer the question.
6. Do not create a visualization unless it improves the answer.
7. When you have enough evidence, produce a concise candidate answer.
"""

def agent_node(state: AgentState) -> dict:

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]

    reflection = state.get("reflection")

    if reflection:
        messages.append(
            SystemMessage(
                content=f"""
            The previous candidate answer was rejected.

            Evaluator feedback:
            {reflection}

            Address this feedback.
            Use additional tools if necessary.
            """
            )
        )

    response = llm_with_tools.invoke(messages)

    updates = {
        "messages": [response],
        "iterations": state.get("iterations", 0) + 1,
        "reflection": None
    }

    if not response.tool_calls:
        updates["candidate_answer"] = response.content
    print(updates)
    return updates

def condition_tools_node(state: AgentState) -> str:
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return 'reflection'
    return 'tools'


def reflection_node(state: AgentState) -> AgentState:
    prompt= f"""
        You are a strict analytics evaluator.

        Your job is to determine whether the current analytical answer
        fully satisfies the user's original question and is supported by
        the available evidence.

        Evaluate:

        1. Intent satisfaction
        - Does the answer actually answer what the user asked?
        - Pay attention to distinctions such as what, why, how much,
            when, comparison, ranking, etc.

        2. Evidence sufficiency
        - Are the SQL results and analytical results sufficient to support
            the claims in the answer?
        - Do not approve unsupported conclusions.

        3. Analytical completeness
        - Is an important analysis still missing?
        - For example, identifying that revenue decreased is not sufficient
            if the user asked why it decreased.

        4. Consistency
        - Does the candidate answer agree with the retrieved results?

        Return:
        - approved=True only if the answer sufficiently answers the question.
        - approved=False otherwise.
        - If rejected, provide specific actionable feedback explaining what
        is missing or incorrect.

        Do not propose an answer to the user yourself.
        Do not invent missing data.
        Every factual claim in the candidate answer must be supported by the evidence.
        Do not approve invented units, currencies, dates, labels, or business interpretations.

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

# nodes.py

def condition_reflection_node(state: AgentState) -> str:
    if state['approved']:
        return "passed"
    return 'return_to_agent'



def tools_node(state: AgentState) -> dict:

    last_message = state["messages"][-1]

    messages = []
    sql_history = []

    for tool_call in last_message.tool_calls:

        tool_name = tool_call["name"]
        args = tool_call["args"]

        if tool_name == "execute_sql":

            query = args["query"]

            result = execute_sql.invoke({
                "query": query
            })

            # Save structured evidence
            sql_history.append({
                "query": query,
                "result": result
            })

            # Also create ToolMessage so agent sees result
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )

        elif tool_name == "get_db_context":

            result = get_db_context.invoke(args)

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )
    print(messages, sql_history)
    return {
        "messages": messages,
        "sql_history": sql_history
    }

graph = StateGraph(AgentState)
graph.add_node('agent_node', agent_node)
graph.add_node('tools_node', tools_node)
graph.add_node('reflection_node', reflection_node)

graph.add_edge(START, 'agent_node')
graph.add_edge('tools_node', 'agent_node')
graph.add_conditional_edges('agent_node', condition_tools_node, {'reflection': 'reflection_node', 'tools': 'tools_node'})
graph.add_conditional_edges('reflection_node', condition_reflection_node, {'passed': END, 'return_to_agent': 'agent_node'})
app = graph.compile()

