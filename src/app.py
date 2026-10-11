from src.agent.graph import build_graph
from src.services.agent_service import AgentService
from src.agent.llm import llm
from src.tools.tools import tools
from src.persistence.repositories.message_repository import MessageRepository
from src.persistence.repositories.session_repository import SessionRepository
from src.persistence.connection import create_connection_factory
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("DB_URL")

connection_factory = create_connection_factory(db_url)
message_repo = MessageRepository(connection_factory)
session_repo = SessionRepository(connection_factory)
graph = build_graph(llm, tools)
agent_service = AgentService(graph, session_repo, message_repo)