# Analytics Agent

An AI analytics assistant that answers business questions using a sample e-commerce database. Ask a question in the Jupyter notebook and the agent can inspect the database schema, run read-only SQL, and review its answer against the query results.

## What it demonstrates

- A tool-using agent workflow built with **LangGraph** and **LangChain**
- Local language model integration through **Ollama**
- PostgreSQL analytics with SQL safety checks, a query timeout, and a result limit
- An evaluation step that checks whether an answer is supported by the data
- Reproducible sample business data for exploring sales trends

## Tech stack

Python · LangGraph · LangChain · Ollama · PostgreSQL · Docker Compose · Jupyter

## Get started

### Requirements

- Python 3.11 or newer
- Docker Compose
- [Ollama](https://ollama.com/) with the model you plan to use

### Setup

1. Create your local environment file and configure matching database credentials:

   ```bash
   cp .env.example .env
   ```

   Set `POSTGRES_PASSWORD` and use the same password in `DB_URL`. The example model is `qwen2.5:7b-instruct`; set `MODEL_NAME` to a model available in your Ollama installation.

2. Start PostgreSQL and install the Python dependencies:

   ```bash
   docker compose up -d
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create the sample data:

   ```bash
   python scripts/seed_business_data.py
   ```

   **This resets the sample business tables before inserting data.**

4. Start Jupyter from the project root, open `agent.ipynb`, and run its cells:

   ```bash
   jupyter notebook
   ```

The notebook includes an example question comparing product category sales from June to July 2026. Change `user_question` to explore other questions.

## How it works

The agent receives a question, gets the database schema and guidance, and uses SQL tools when it needs data. A reflection step checks the candidate answer against the question and query history; if needed, the agent can revise its analysis.

SQL execution accepts read-only `SELECT` and `WITH` queries, limits execution time to 3 seconds, and returns at most 500 rows.

## Project structure

```text
src/
  agent/       Agent graph, prompts, model setup, and workflow nodes
  database/   PostgreSQL connection, SQL guardrails, and query executor
  services/   Agent service interface
  tools/      SQL execution and database schema context tools
database/     PostgreSQL schema
scripts/      Sample business data generator
agent.ipynb   Example notebook
compose.yaml  Local PostgreSQL service
```
