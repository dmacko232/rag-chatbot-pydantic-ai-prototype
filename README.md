# Telekom RAG Chatbot

A RAG (Retrieval-Augmented Generation) chatbot over Deutsche Telekom press releases. Built with PydanticAI, FastAPI, Next.js, Azure OpenAI, and Cohere.

For description of what was done how see
- docs/approach_report.md
- docs/future_steps.md

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+
- Azure OpenAI API access
- Cohere API key

## Getting Started

### 1. Clone and configure

```bash
cp .env.example .env
```

Fill in your API keys in `.env`:

| Variable | Description |
|---|---|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `COHERE_API_KEY` | Cohere API key (embeddings + reranking) |
| `JWT_SECRET_KEY` | Any random string for signing auth tokens |

### 2. Install dependencies

```bash
uv sync --all-extras
cd src/frontend && npm install && cd ../..
```

### 3. Run the data pipeline

This loads press releases from `data/raw/`, chunks them with the LLM, embeds with Cohere, and indexes into SQLite.

```bash
PYTHONPATH=src uv run python -m data_pipeline.main
```

### 4. Start the backend

```bash
PYTHONPATH=src uv run uvicorn backend.main:app --reload
```

Backend runs at http://localhost:8000. Swagger docs at http://localhost:8000/docs.

### 5. Start the frontend

```bash
cd src/frontend && npm run dev
```

Frontend runs at http://localhost:3000.

### 6. Log in

A test account is seeded automatically: username `test`, password `test`.

## One-Command Start

Alternatively, run everything at once:

```bash
./run.sh
```

## Docker

```bash
docker compose up --build
```

Services: backend (:8000), frontend (:3000), Arize Phoenix (:6006).

## Running Tests

```bash
# Python tests (backend + data pipeline)
PYTHONPATH=src OPENAI_API_KEY=dummy uv run pytest tests/ -v

# Frontend tests
cd src/frontend && npm test
```

## Project Structure

```
config/              # Prompt configs (YAML)
data/raw/            # Raw press release text files
eval/                # Evaluation questions + runner
src/
  shared/            # Config, DB, models, prompt loader
  data_pipeline/     # Ingestion pipeline (interfaces + implementations)
  backend/           # FastAPI app (DDD layers)
    domain/          # Models, interfaces
    application/     # Use cases, tools, services, repositories
    presentation/    # Routes, dependencies
  frontend/          # Next.js app
tests/
  unit/              # Unit tests
  component/         # Integration tests (DB)
  api/               # API endpoint tests
```

## Tech Stack

- **LLM**: Azure OpenAI (GPT-4o)
- **Agent**: PydanticAI
- **Embeddings & Reranking**: Cohere
- **Backend**: FastAPI, SQLModel, SQLite + sqlite-vec
- **Frontend**: Next.js, React, Tailwind CSS
- **Observability**: Arize Phoenix
