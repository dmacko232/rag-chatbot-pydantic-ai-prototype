# RAG Chatbot — Design Document

## Overview

A RAG chatbot for Telekom press releases, built with **PydanticAI**, **FastAPI**, and **Next.js**. Uses **Azure OpenAI** for the LLM, **Cohere** for embeddings and reranking, **SQLite** (vector extension) as the vector store, and **Arize Phoenix** for observability and eval experimentation.

---

## Project Structure

```
src/
├── shared/          # models, utils, and config shared between pipeline & backend
├── data_pipeline/   # ingestion and indexing pipeline
├── backend/         # FastAPI application
└── frontend/        # Next.js application
```

---

## Architecture

### Shared (`src/shared`)

- Data models used by both pipeline and backend: `Document`, `Chunk`, etc.
- Common utilities (e.g. vector store client, Cohere client wrappers)

### Data Pipeline (`src/data_pipeline`)

- **Input**: Local disk (abstracted so it's swappable to Azure Blob)
- **Pattern**: Pipeline pattern — each step is a class, pipeline orchestrates them
- **Chunking**: Input is HTML that has been parsed to plain text (formatting lost). Use LLM to infer meaningful chunk boundaries based on semantic meaning, producing chunks suitable for search.
- **Embeddings**: Cohere embedding model
- **Vector store**: SQLite vector extension
- **RAPTOR**: Generate hierarchical summaries for answering global/abstract questions
- **Small-to-big**: Store smaller chunks for retrieval, larger surrounding context for LLM
- **Observability**: Arize Phoenix tracing

### Backend (`src/backend`)

- **Framework**: FastAPI with streaming responses
- **LLM**: Azure OpenAI via PydanticAI, prompted for Telekom press releases
- **Tool-call limit**: Max 3 tool calls per turn
- **Auth**: JWT-based login/registration (include a pre-seeded test account)
- **Validation**: Pydantic models / dataclasses throughout
- **DB**: SQLModel — `User`, `Session`, `Response` tables; Repository + Unit of Work patterns
- **Structure (DDD)**: Three layers:
  - **Presentation** (API routes) — each route maps to a use case; handles DB persistence
  - **Application** (use cases + tools) — agents live under use cases
  - **Domain** (models/interfaces)
- **Retrieval tool** (Pipeline-pattern class):
  1. Hybrid search (vector + keyword)
  2. Cohere reranker
  3. Score thresholding — drop anything below **0.3** reranker score
- **Citations**: LLM generates inline citations after each statement, referencing source chunks. Response is nicely formatted markdown.
- **DI**: All classes behind interfaces for dependency injection
- **Chat history**: Separate endpoint(s) and use cases
- **Observability**: Arize Phoenix (tracing + eval experiments)
- **Tests**: Unit (fully mocked) → Component (mocked externals) → Integration (real services) → API (endpoint tests)

### Frontend (`src/frontend`)

- **Framework**: Next.js / React (TypeScript)
- **Auth**: Login/register flow (test account pre-seeded)
- **Chat UI**: Markdown rendering, inline citations with source references, thinking indicator
- **History**: View and reopen past chats

### Infrastructure

- Docker Compose packaging for all services
- Secrets in `.env` files

### Tooling & Dev Practices

- **Dependency management**: Poetry
- **Type checking**: ty
- **Linting/formatting**: Ruff
- **Pre-commit hook**: Runs Ruff + ty on every commit
- **Commits**: Small, focused commits (one logical change per commit)

---

## Implementation Steps

### Phase 0 — Setup

- [ ] Init Poetry project, configure Ruff + ty
- [ ] Set up pre-commit hook (Ruff + ty)
- [ ] Set up Docker Compose skeleton (backend, frontend, Phoenix)
- [ ] Create `.env.example` with placeholder secrets (Azure OpenAI, Cohere keys)
- [ ] Create `src/` directory structure (`shared`, `data_pipeline`, `backend`, `frontend`)

### Phase 1 — Data Analysis

- [ ] Explore and document the data in `data/raw` (formats, fields, volumes, quality)
- [ ] Produce a short analysis report / notebook with findings
- [ ] **CHECKPOINT** — review analysis results before proceeding

### Phase 2 — Data Pipeline

- [ ] Define shared data models in `src/shared` (`Document`, `Chunk`, etc.)
- [ ] Implement pipeline framework (base `Step` and `Pipeline` classes)
- [ ] Implement loading step (local disk reader, abstracted for Blob)
- [ ] Implement LLM chunking step (semantic boundary detection on parsed HTML text)
- [ ] Implement Cohere embedding step
- [ ] Set up SQLite vector store and write indexing step
- [ ] Implement RAPTOR summarisation step
- [ ] Wire up Arize Phoenix tracing

### Phase 3 — Backend

- [ ] Scaffold FastAPI app with DDD folder structure under `src/backend`
- [ ] Implement auth (JWT, user registration, test account seed)
- [ ] Define SQLModel tables + repository/UoW layer
- [ ] Build retrieval tool (hybrid search → Cohere reranker → 0.3 threshold)
- [ ] Implement chat use case with PydanticAI agent + streaming (3-call tool limit)
- [ ] Prompt engineering: inline citations, markdown-formatted responses
- [ ] Implement chat history endpoints
- [ ] Add Arize Phoenix instrumentation
- [ ] Write unit, component, integration, and API tests

### Phase 4 — Frontend

- [ ] Scaffold Next.js app under `src/frontend`
- [ ] Build login/register pages
- [ ] Build chat UI (markdown rendering, inline citations, thinking state)
- [ ] Build chat history sidebar
- [ ] Connect to backend API (auth + streaming chat)

### Phase 5 — Polish & Docs

- [ ] Finalise Docker Compose (all services run together)
- [ ] Write workflow documentation
- [ ] Document limitations and future steps
