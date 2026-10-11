from fastapi import FastAPI

from src.api.routes.query import router as query_router
from src.api.routes.sessions import router as sessions_router


app = FastAPI(
    title="RAG Analytics Agent",
    version="0.1.0"
)

app.include_router(
    query_router,
    prefix="/api"
)

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


app.include_router(
    sessions_router,
    prefix="/api"
)
