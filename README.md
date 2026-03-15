# Telekom RAG Chatbot

A RAG (Retrieval-Augmented Generation) chatbot over Deutsche Telekom press releases. Built with PydanticAI, FastAPI, Next.js, Azure OpenAI, and Cohere.

For description of what was done and how, see:
- `docs/approach_report.md`
- `docs/future_steps.md`

## Quick Start

### 1. Configure

```bash
cp .env.example .env
```

Fill in your API keys in `.env`:

| Variable | Description |
|---|---|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `COHERE_API_KEY` | Cohere API key (embeddings + reranking) |

### 2. Run

```bash
./run.sh
```

This starts everything (uses Docker Compose if available, otherwise runs locally):
- **Data pipeline** — loads, chunks, embeds, and indexes press releases
- **Backend** — FastAPI API on http://localhost:8000 (Swagger at http://localhost:8000/docs)
- **Frontend** — Next.js app on http://localhost:3000
- **Phoenix** — Observability dashboard on http://localhost:6006 (Docker only)

### 3. Log in

Open http://localhost:3000 and use the test account:
- **Username:** `test`
- **Password:** `test`

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (recommended)
- Or: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 20+ (for local mode)

## Local Development (without Docker)

```bash
# Install dependencies
uv sync --all-extras
cd src/frontend && npm install && cd ../..

# Run pipeline
PYTHONPATH=src uv run python -m data_pipeline.main

# Start backend
PYTHONPATH=src uv run uvicorn backend.main:app --reload

# Start frontend (separate terminal)
cd src/frontend && npm run dev
```

## Running Tests

```bash
# Python tests (backend + data pipeline)
uv run pytest tests/ -v

# Frontend tests
cd src/frontend && npm test
```

## Project Structure

```
config/              # App config (prompts, retrieval, chunking)
data/raw/            # Raw press release text files
docker/              # Dockerfiles (backend, pipeline, frontend)
eval/                # Evaluation questions + runner
src/
  shared/            # Config, DB, models, prompt loader
  data_pipeline/     # Ingestion pipeline
    models.py        # Data models
    interfaces.py    # Step interfaces (ABCs)
    pipeline.py      # Orchestrator
    steps/           # Implementations (loader, chunker, embedder, ...)
  backend/           # FastAPI app (DDD layers)
    domain/          # SQLModel tables
    application/     # Use cases, tools, services, repositories, DTOs
    presentation/    # Routes, dependencies, API schemas
  frontend/          # Next.js app
tests/
  unit/              # Unit tests
  component/         # Integration tests (DB)
  api/               # API endpoint tests
```

## Tech Stack

- **LLM**: Azure OpenAI (GPT-4o-mini)
- **Agent**: PydanticAI
- **Embeddings & Reranking**: Cohere
- **Backend**: FastAPI, SQLModel, SQLite + sqlite-vec + FTS5
- **Frontend**: Next.js, React, Tailwind CSS
- **Observability**: Arize Phoenix
