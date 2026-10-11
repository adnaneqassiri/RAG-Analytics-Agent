from src.agent.graph import build_graph
from src.services.agent_service import AgentService
from src.agent.llm import llm
from src.tools.tools import tools

graph = build_graph(llm, tools)
agent_service = AgentService(graph)