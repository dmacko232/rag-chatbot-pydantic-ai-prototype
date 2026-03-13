import logging
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass

import cohere
from sqlmodel import Session, select, text

from shared.config import Settings
from shared.models import Chunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: int
    content: str
    content_for_llm: str
    score: float
    source_file: str
    document_id: int


class RetrievalStep(ABC):
    @abstractmethod
    def execute(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]: ...


class VectorSearchStep(RetrievalStep):
    def __init__(self, db_session: Session, cohere_client: cohere.Client, embed_model: str, top_k: int = 30) -> None:
        self._db_session = db_session
        self._cohere = cohere_client
        self._embed_model = embed_model
        self._top_k = top_k

    def execute(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        response = self._cohere.embed(texts=[query], model=self._embed_model, input_type="search_query")
        query_embedding = response.embeddings[0]
        query_bytes = struct.pack(f"{len(query_embedding)}f", *query_embedding)

        rows = self._db_session.exec(
            text(
                """
                SELECT chunk_id, distance
                FROM chunk_embeddings
                WHERE embedding MATCH :query
                ORDER BY distance
                LIMIT :k
                """
            ),
            params={"query": query_bytes, "k": self._top_k},
        ).all()

        results: list[RetrievedChunk] = []
        for chunk_id, distance in rows:
            chunk = self._db_session.get(Chunk, chunk_id)
            if chunk and chunk.document:
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        content_for_llm=chunk.content_for_llm,
                        score=1.0 - distance,
                        source_file=chunk.document.source_file,
                        document_id=chunk.document_id,
                    )
                )
        return results


class KeywordSearchStep(RetrievalStep):
    """Simple keyword-based search as a fallback/complement to vector search."""

    def __init__(self, db_session: Session, top_k: int = 20) -> None:
        self._db_session = db_session
        self._top_k = top_k

    def execute(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        terms = [t.strip() for t in query.lower().split() if len(t.strip()) > 2]
        if not terms:
            return candidates

        like_clauses = " OR ".join(f"chunk.content LIKE :t{i}" for i in range(len(terms)))
        params = {f"t{i}": f"%{term}%" for i, term in enumerate(terms)}
        params["limit"] = self._top_k

        rows = self._db_session.exec(
            text(f"SELECT id FROM chunk WHERE {like_clauses} LIMIT :limit"),
            params=params,
        ).all()

        existing_ids = {c.chunk_id for c in candidates}
        for (chunk_id,) in rows:
            if chunk_id not in existing_ids:
                chunk = self._db_session.get(Chunk, chunk_id)
                if chunk and chunk.document:
                    candidates.append(
                        RetrievedChunk(
                            chunk_id=chunk.id,
                            content=chunk.content,
                            content_for_llm=chunk.content_for_llm,
                            score=0.0,
                            source_file=chunk.document.source_file,
                            document_id=chunk.document_id,
                        )
                    )
        return candidates


class CohereRerankStep(RetrievalStep):
    def __init__(self, cohere_client: cohere.Client, model: str, top_n: int = 10) -> None:
        self._cohere = cohere_client
        self._model = model
        self._top_n = top_n

    def execute(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not candidates:
            return []

        docs = [c.content for c in candidates]
        response = self._cohere.rerank(query=query, documents=docs, model=self._model, top_n=self._top_n)

        reranked: list[RetrievedChunk] = []
        for result in response.results:
            candidate = candidates[result.index]
            candidate.score = result.relevance_score
            reranked.append(candidate)

        return reranked


class ThresholdStep(RetrievalStep):
    def __init__(self, threshold: float = 0.3) -> None:
        self._threshold = threshold

    def execute(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        filtered = [c for c in candidates if c.score >= self._threshold]
        logger.info("Threshold %.2f: %d → %d chunks", self._threshold, len(candidates), len(filtered))
        return filtered


class RetrievalPipeline:
    """Orchestrates the retrieval steps: vector search → keyword search → rerank → threshold."""

    def __init__(self, steps: list[RetrievalStep]) -> None:
        self._steps = steps

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        candidates: list[RetrievedChunk] = []
        for step in self._steps:
            candidates = step.execute(query, candidates)
        return candidates
