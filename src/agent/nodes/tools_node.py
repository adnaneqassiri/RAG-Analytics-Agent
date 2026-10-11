from langchain_core.messages import ToolMessage
from src.agent.state import AgentState
from src.tools import get_db_context, execute_sql

def tools_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    messages = []
    sql_history = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        if tool_name == "execute_sql":
            query = args["query"]
            result = execute_sql.invoke({"query": query})
            sql_history.append({
                "query": query,
                "result": result
            })            
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
    return {
        "messages": messages,
        "sql_history": sql_history
    }