# Approach Report

## How This Project Was Built

1. **Wrote design document** — Outlined the full architecture (data pipeline, backend, frontend), technology choices (Azure OpenAI, Cohere, PydanticAI, FastAPI, Next.js, SQLite vector), and phased implementation plan.

2. **Prompted Claude to do data analysis** — Explored the 254 raw press release files: computed statistics (word counts, structure patterns, outliers), identified topic categories, analyzed extractable metadata fields (year, business segment, document type), and documented findings with pipeline implications.

3. **Rewrote design document based on analysis** — Added Document/Chunk table schemas with metadata columns, a SQL tool for aggregation queries, an evaluation phase with 30 diverse questions, and refined the chunking and retrieval strategy based on what the data looked like.

4. **Prompted Claude to write data pipeline, backend, frontend, and evaluation** — Implemented all phases: project setup with uv/Ruff/ty, the ingestion pipeline (LLM chunking, Cohere embeddings, RAPTOR, SQLite vector store), the FastAPI backend (DDD layers, PydanticAI agent, JWT auth, retrieval + SQL tools), the Next.js frontend (chat UI with markdown/citations, auth, history), and a 30-question eval set with correctness and precision@10 measurement.

## Key design choices

- I used sqlite DB as it can be easily used for vector search + keeping memory (chat history) + we can even query the tables for analytical queries
- I went with typical RAG pipeline + I used LLM to infer metadata for the press releases.
    - we have data pipeline and backend
    - for chunking I used LLM chunking as these docs had no structure. I also wanted to try it out.
    - I also used RAPTOR as a method to generate summaries of articles. I wanted to try it out -- it is a method that can help with global summarizing quesitons.
    - used LLM to extract various metadata for the documents -- retrieval can use filtering, but users can also ask Qs like "how many documents are about X?"
    - then we have agent with retrieval tool and SQL tool
    - retrieval tool is typical easy setup of hybrid search + reranking + thresholding based on reranker score
- backend has typical design of being divided into 3 layers