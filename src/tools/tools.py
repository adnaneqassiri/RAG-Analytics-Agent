from src.tools.rag_tool import create_rag_tool
from src.tools.sql_tool import create_sql_tool
from src.database.executor import SQLExecutor
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("DB_URL")

sql_executor = SQLExecutor(
    db_url=db_url,
    timeout_ms=3000,
    max_rows=500,
)

get_db_context = create_rag_tool()
execute_sql = create_sql_tool(sql_executor)

tools = [execute_sql, get_db_context]