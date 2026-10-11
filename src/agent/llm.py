from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()
model_name = os.getenv("MODEL_NAME")


llm = ChatOllama(model=model_name, temperature=0)