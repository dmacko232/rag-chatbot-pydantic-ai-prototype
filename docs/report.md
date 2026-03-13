# Approach Report

## How This Project Was Built

1. **Wrote a design document** — outlined the full architecture (data pipeline, backend, frontend), tech stack (PydanticAI, FastAPI, Next.js, Azure OpenAI, Cohere, SQLite), project structure, and phased implementation plan.

2. **Prompted Claude to do data analysis** — explored the 254 raw press release files: computed statistics (word counts, structure patterns, outliers), identified topic categories via keyword heuristics, analysed extractable metadata (year, business segment, document type), and documented findings with pipeline implications.

3. **Rewrote the design document based on analysis** — added `Document`/`Chunk` table schemas with metadata columns, a SQL tool for aggregation queries, Pydantic Settings for configuration, and an evaluation phase with 30 diverse questions measuring correctness and precision@10.

4. **Prompted Claude to implement the full system** — data pipeline (cleaning, LLM chunking, Cohere embeddings, SQLite vector store, RAPTOR summaries), backend (FastAPI with DDD, JWT auth, PydanticAI agent with retrieval + SQL tools, streaming, chat history), frontend (Next.js with login, chat UI, history), and evaluation suite.
