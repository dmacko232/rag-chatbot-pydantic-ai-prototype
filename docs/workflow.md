# Workflow

## Quick Start

```bash
# 1. Copy env file and fill in API keys
cp .env.example .env

# 2. Run everything
./run.sh
```

This will install dependencies, run the data pipeline, and start the backend + frontend.

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API docs (Swagger)**: http://localhost:8000/docs
- **Test account**: username `test`, password `test`

## Docker

```bash
docker compose up --build
```

## Individual Components

### Data Pipeline

```bash
PYTHONPATH=src uv run python -m data_pipeline.main
```

Loads raw text files from `data/raw/`, chunks them via LLM, embeds with Cohere, and indexes into SQLite.

### Backend

```bash
PYTHONPATH=src uv run uvicorn backend.main:app --reload
```

### Frontend

```bash
cd src/frontend && npm run dev
```

### Tests

```bash
PYTHONPATH=src uv run pytest tests/ -v
```

### Evaluation

```bash
PYTHONPATH=src uv run python eval/run_eval.py
```

Runs 30 eval questions, outputs `eval/results.json` with correctness and precision@10 scores.

## Limitations

- SQLite is single-writer; not suitable for high-concurrency production use
- RAPTOR summaries are generated once at pipeline time — not updated dynamically
- Keyword search is basic LIKE matching, not full-text search
- No rate limiting on API endpoints
- Frontend does not handle token refresh

## Future Steps

- Replace SQLite with PostgreSQL + pgvector for production
- Add full-text search (SQLite FTS5 or Elasticsearch)
- Implement token refresh flow
- Add rate limiting and request validation
- Run Arize Phoenix evals in CI
- Explore fine-tuning the reranker threshold based on eval results
