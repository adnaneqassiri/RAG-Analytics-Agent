# Analytics Agent

A prototype analytics agent that uses LangGraph, Ollama, and PostgreSQL to answer questions about a sample e-commerce database. The agent can inspect the schema, run read-only SQL queries, and evaluate whether its answer is supported by query results.

## Requirements

- Python 3.11 or newer
- Docker Compose
- Ollama, with the model configured by `MODEL_NAME` available locally

## Setup

1. Copy `.env.example` to `.env`. Set `DB_URL`, `MODEL_NAME`, and `POSTGRES_PASSWORD` for your local setup. The password in `POSTGRES_PASSWORD` must match the password in `DB_URL`. `.env` is ignored by Git.
2. Start PostgreSQL:

   ```bash
   docker compose up -d
   ```

   The example uses `analytics123` as a development-only database password. Set your own `POSTGRES_PASSWORD` in `.env` and use the same password in `DB_URL` for local use. Do not use the example password for a public or production database.
3. Install Python dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Seed the database with sample data:

   ```bash
   python scripts/seed_business_data.py
   ```
5. Make sure Ollama is running and the model named by `MODEL_NAME` is available. The example uses `qwen2.5:7b-instruct`.
6. Open `agent.ipynb` in Jupyter and run its cells to use the agent.

The seed script clears existing rows in the sample business tables before inserting new data.

## Project files

- `src/graph.py`: agent and reflection workflow
- `src/tools.py`: database context and read-only SQL tool
- `src/llm.py`: Ollama model configuration
- `database/init.sql`: PostgreSQL schema
- `scripts/seed_business_data.py`: deterministic sample-data generator
- `agent.ipynb`: example invocation
