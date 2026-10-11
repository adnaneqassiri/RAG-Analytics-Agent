from fastapi import FastAPI

from src.api.routes.query import router as query_router


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