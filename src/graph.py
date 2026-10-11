from langgraph.graph import StateGraph, END, START
from src.agent.state import AgentState
from src.agent.nodes.agent_node import agent_node
from src.agent.nodes.tools_node import tools_node
from src.agent.nodes.reflection_node import reflection_node

def condition_tools_node(state: AgentState) -> str:
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return 'reflection'
    return 'tools'

def condition_reflection_node(state: AgentState) -> str:
    if state['approved']:
        return "passed"
    return 'return_to_agent'


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node('agent_node', agent_node)
    graph.add_node('tools_node', tools_node)
    graph.add_node('reflection_node', reflection_node)

    graph.add_edge(START, 'agent_node')
    graph.add_edge('tools_node', 'agent_node')
    graph.add_conditional_edges(
        'agent_node',
        condition_tools_node, 
        {
            'reflection': 'reflection_node', 
            'tools': 'tools_node'
        })

    graph.add_conditional_edges(
        'reflection_node', 
        condition_reflection_node, 
        {
            'passed': END, 
            'return_to_agent': 'agent_node'
        })

    app = graph.compile()
    
    return app
