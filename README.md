# Analytics Agent

An AI assistant for asking questions about sample e-commerce data. It uses an LLM to plan analysis, query PostgreSQL with read-only SQL, and check its answer against the query results.

## Current project status

This is a working local prototype with both a Jupyter example and a FastAPI interface. The API can create sessions, answer questions in a session, and return saved conversation messages. Session and message data are stored in PostgreSQL.

## Highlights

- **Agent workflow:** LangGraph, LangChain tools, and a reflection step
- **Local model:** Ollama, configurable with `MODEL_NAME`
- **Database:** PostgreSQL with SQL checks, a 3-second query timeout, and a 500-row result limit
- **API:** FastAPI endpoints for health checks, session creation, questions, and conversation history
- **Sample data:** deterministic e-commerce data for exploring business questions
- **RAG groundwork:** the agent receives database schema context to guide SQL generation, and the database defines a pgvector-ready `knowledge_chunks` table. Document ingestion, embedding generation, and vector retrieval are planned, but not implemented yet.

## Tech stack

Python · FastAPI · LangGraph · LangChain · Ollama · PostgreSQL · Docker Compose

## Setup

### Requirements

- Python 3.11 or newer
- Docker Compose
- [Ollama](https://ollama.com/) with a model available locally

### Install and start the database

1. Copy the environment template and set `DB_URL`, `POSTGRES_PASSWORD`, and `MODEL_NAME`. The PostgreSQL password in `DB_URL` must match `POSTGRES_PASSWORD`.

   ```bash
   cp .env.example .env
   ```

2. Start PostgreSQL and install dependencies:

   ```bash
   docker compose up -d
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Populate the database with sample data:

   ```bash
   python scripts/seed_business_data.py
   ```

   The seed script clears and recreates the sample business data.

## Run the API

From the project root, start the development server:

```bash
uvicorn src.api.app:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check that the API is running |
| `POST` | `/api/sessions` | Create a conversation and receive its UUID |
| `POST` | `/api/sessions/{session_id}/messages` | Ask a question in that conversation |
| `GET` | `/api/sessions/{session_id}/messages` | Retrieve saved conversation messages |

Send questions as JSON, for example:

```json
{"message": "Which product category had the highest sales in 2026?"}
```

## Use the notebook

Start Jupyter from the project root, open `agent.ipynb`, and run its cells:

```bash
jupyter notebook
```

The notebook includes an example sales comparison. Change `user_question` to explore other questions.

## Project structure

```text
src/
  agent/        LangGraph workflow, model setup, prompts, and nodes
  api/          FastAPI application, routes, and request/response schemas
  database/     PostgreSQL connection, SQL guardrails, and query executor
  persistence/  Session and message repositories
  services/     Agent orchestration and conversation handling
  tools/        SQL execution and database schema context (RAG groundwork)
database/       PostgreSQL schema
scripts/        Sample business data generator
agent.ipynb     Notebook example
compose.yaml    Local PostgreSQL service
```
