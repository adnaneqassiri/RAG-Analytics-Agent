from langchain_core.messages import ToolMessage
from src.agent.state import AgentState


def create_tools_node(tools):

    tool_map = {
        tool.name: tool
        for tool in tools
    }

    def tools_node(state: AgentState) -> dict:

        last_message = state["messages"][-1]

        messages = []
        sql_history = []

        for tool_call in last_message.tool_calls:

            tool_name = tool_call["name"]
            args = tool_call["args"]

            if tool_name not in tool_map:
                raise ValueError(
                    f"Unknown tool: {tool_name}"
                )

            tool = tool_map[tool_name]

            result = tool.invoke(args)

            if tool_name == "execute_sql":
                sql_history.append({
                    "query": args["query"],
                    "result": result
                })

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

    return tools_node