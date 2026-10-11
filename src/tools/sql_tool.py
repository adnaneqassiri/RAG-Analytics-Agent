from langchain_core.tools import tool

def create_sql_tool(executor):
    @tool
    def execute_sql(query: str ) -> str:
        """
        Execute a safe, read-only SQL query against the analytics database.
        Returns the query result or an error message.
        please pass in 'query' for the sql query
        """
        result = executor.execute(query)
        print(result)
        return result
        
    return execute_sql