from langchain_core.messages import HumanMessage, AIMessage

def to_langchain_messages(messages):
    result = []
    for message in messages:

        if message["role"] == "user":
            result.append(
                HumanMessage(
                    content=message["content"]
                )
            )
        elif message["role"] == "assistant":
            result.append(
                AIMessage(
                    content=message["content"]
                )
            )

    return result

class AgentService:
    def __init__(
        self,
        graph,
        session_repository,
        message_repository,
    ):
        self.graph = graph
        self.session_repository = session_repository
        self.message_repository = message_repository

    def run(
        self,
        question: str,
        session_id: str
    ):

        # 1. Verify session
        session = self.session_repository.get(
            session_id
        )

        if session is None:
            raise ValueError("Session not found")


        # 2. Load previous conversation
        history = self.message_repository.list_by_session(
            session_id
        )

        messages = to_langchain_messages(
            history
        )


        # 3. Add current user message
        messages.append(
            HumanMessage(content=question)
        )


        # 4. Save it
        self.message_repository.create(
            session_id=session_id,
            role="user",
            content=question
        )


        # 5. Invoke agent
        result = self.graph.invoke(
            {
                "messages": messages,
                "question": question,
                "iterations": 0,
                "sql_history": []
            }
        )


        # 6. Extract final answer
        answer = result["candidate_answer"]


        # 7. Persist assistant response
        self.message_repository.create(
            session_id=session_id,
            role="assistant",
            content=answer
        )


        # 8. Return application result
        return {
            "answer": answer,
            "sql_history": result.get(
                "sql_history",
                []
            )
        }