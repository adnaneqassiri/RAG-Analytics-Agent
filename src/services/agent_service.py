class AgentService:

    def __init__(self, graph):
        self.graph = graph

    def run(
        self,
        question: str,
        session_id: str
    ):

        result = self.graph.invoke(
            {
                "messages": question,
                "question": question,
            }, 
            config={
                "recursion_limit": 20
            }
        )

        return result