from langchain_core.messages import SystemMessage
from src.agent.state import AgentState
from src.agent.prompts.agent import SYSTEM_PROMPT
from src.tools.tools import tools
from src.agent.llm import llm



def create_agent_node(llm, tools): 
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT),*state["messages"]]
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
    
    return agent_node