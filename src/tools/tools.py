from src.tools.rag_tool import create_rag_tool
from src.tools.sql_tool import create_sql_tool
from src.database.executor import SQLExecutor
from src.results.manager import ResultsManager
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("DB_URL")

sql_executor = SQLExecutor(
    db_url=db_url,
    timeout_ms=3000,
    max_rows=500,
)

results_manager = ResultsManager(
    base_dir=".runtime/results",
    ttl_seconds=600,
)

get_db_context = create_rag_tool()
execute_sql = create_sql_tool(
    executor=sql_executor,
    results_manager=results_manager,
)

tools = [execute_sql, get_db_context]