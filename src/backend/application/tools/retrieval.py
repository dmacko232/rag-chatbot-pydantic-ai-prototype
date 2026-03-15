import logging
import struct
from dataclasses import dataclass, field

import cohere
from sqlmodel import Session, text

from shared.models import Chunk

logger = logging.getLogger(__name__)


@dataclass
class MetadataFilter:
    year: int | None = None
    business_segment: str | None = None
    document_type: str | None = None

    @property
    def is_empty(self) -> bool:
        return self.year is None and self.business_segment is None and self.document_type is None


@dataclass
class RetrievedChunk:
    chunk_id: int
    content: str
    content_for_llm: str
    score: float
    source_file: str
    document_id: int
    year: int | None = None
    business_segment: str | None = None
    document_type: str | None = None


class HybridSearch:
    """Combines vector search and BM25 using Reciprocal Rank Fusion (RRF).

    RRF score = alpha * 1/(k + rank_vector) + (1 - alpha) * 1/(k + rank_bm25)
    where k is a smoothing constant (typically 60).
    """

    def __init__(
        self,
        db_session: Session,
        cohere_client: cohere.Client,
        embed_model: str,
        vector_top_k: int = 100,
        bm25_top_k: int = 100,
        rrf_k: int = 60,
        rrf_alpha: float = 0.5,
        rrf_top_n: int = 100,
    ) -> None:
        self._db = db_session
        self._cohere = cohere_client
        self._embed_model = embed_model
        self._vector_top_k = vector_top_k
        self._bm25_top_k = bm25_top_k
        self._rrf_k = rrf_k
        self._rrf_alpha = rrf_alpha
        self._rrf_top_n = rrf_top_n

    def search(self, query: str, metadata_filter: MetadataFilter | None = None) -> list[RetrievedChunk]:
        vector_results = self._vector_search(query)
        bm25_results = self._bm25_search(query)

        if metadata_filter and not metadata_filter.is_empty:
            vector_results = self._apply_metadata_filter(vector_results, metadata_filter)
            bm25_results = self._apply_metadata_filter(bm25_results, metadata_filter)

        fused = self._reciprocal_rank_fusion(vector_results, bm25_results)

        logger.info(
            "Hybrid search: %d vector + %d BM25 → %d after RRF (alpha=%.2f, filter=%s)",
            len(vector_results), len(bm25_results), len(fused), self._rrf_alpha,
            metadata_filter if metadata_filter and not metadata_filter.is_empty else "none",
        )
        return fused

    @staticmethod
    def _apply_metadata_filter(
        chunks: list[RetrievedChunk], mf: MetadataFilter
    ) -> list[RetrievedChunk]:
        filtered: list[RetrievedChunk] = []
        for c in chunks:
            if mf.year is not None and c.year != mf.year:
                continue
            if mf.business_segment is not None and c.business_segment != mf.business_segment:
                continue
            if mf.document_type is not None and c.document_type != mf.document_type:
                continue
            filtered.append(c)
        return filtered

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[RetrievedChunk],
        bm25_results: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        k = self._rrf_k
        alpha = self._rrf_alpha

        vector_ranks = {c.chunk_id: rank for rank, c in enumerate(vector_results, start=1)}
        bm25_ranks = {c.chunk_id: rank for rank, c in enumerate(bm25_results, start=1)}

        all_chunks: dict[int, RetrievedChunk] = {}
        for c in vector_results:
            all_chunks[c.chunk_id] = c
        for c in bm25_results:
            if c.chunk_id not in all_chunks:
                all_chunks[c.chunk_id] = c

        rrf_scores: dict[int, float] = {}
        for chunk_id in all_chunks:
            vec_score = alpha * (1.0 / (k + vector_ranks[chunk_id])) if chunk_id in vector_ranks else 0.0
            bm25_score = (1 - alpha) * (1.0 / (k + bm25_ranks[chunk_id])) if chunk_id in bm25_ranks else 0.0
            rrf_scores[chunk_id] = vec_score + bm25_score

        ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[: self._rrf_top_n]

        result: list[RetrievedChunk] = []
        for chunk_id in ranked_ids:
            chunk = all_chunks[chunk_id]
            chunk.score = rrf_scores[chunk_id]
            result.append(chunk)

        return result

    def _vector_search(self, query: str) -> list[RetrievedChunk]:
        response = self._cohere.embed(texts=[query], model=self._embed_model, input_type="search_query")
        query_bytes = struct.pack(f"{len(response.embeddings[0])}f", *response.embeddings[0])

        rows = self._db.exec(
            text(
                """
                SELECT chunk_id, distance
                FROM chunk_embeddings
                WHERE embedding MATCH :query
                ORDER BY distance
                LIMIT :k
                """
            ),
            params={"query": query_bytes, "k": self._vector_top_k},
        ).all()

        results: list[RetrievedChunk] = []
        for chunk_id, distance in rows:
            chunk = self._db.get(Chunk, chunk_id)
            if chunk and chunk.document:
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        content_for_llm=chunk.content_for_llm,
                        score=1.0 - distance,
                        source_file=chunk.document.source_file,
                        document_id=chunk.document_id,
                        year=chunk.document.year,
                        business_segment=chunk.document.business_segment,
                        document_type=chunk.document.document_type,
                    )
                )
        return results

    def _bm25_search(self, query: str) -> list[RetrievedChunk]:
        terms = [t.strip() for t in query.split() if len(t.strip()) > 2]
        if not terms:
            return []

        fts_query = " OR ".join(f'"{t}"' for t in terms)

        rows = self._db.exec(
            text(
                """
                SELECT rowid, bm25(chunk_fts) AS score
                FROM chunk_fts
                WHERE chunk_fts MATCH :query
                ORDER BY score
                LIMIT :k
                """
            ),
            params={"query": fts_query, "k": self._bm25_top_k},
        ).all()

        results: list[RetrievedChunk] = []
        for chunk_id, bm25_score in rows:
            chunk = self._db.get(Chunk, chunk_id)
            if chunk and chunk.document:
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        content_for_llm=chunk.content_for_llm,
                        score=abs(bm25_score),
                        source_file=chunk.document.source_file,
                        document_id=chunk.document_id,
                        year=chunk.document.year,
                        business_segment=chunk.document.business_segment,
                        document_type=chunk.document.document_type,
                    )
                )
        return results


class CohereReranker:
    def __init__(self, cohere_client: cohere.Client, model: str, top_n: int = 10) -> None:
        self._cohere = cohere_client
        self._model = model
        self._top_n = top_n

    def rerank(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
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


class ScoreFilter:
    def __init__(self, threshold: float = 0.3) -> None:
        self._threshold = threshold

    def filter(self, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        filtered = [c for c in candidates if c.score >= self._threshold]
        logger.info("Score filter %.2f: %d → %d chunks", self._threshold, len(candidates), len(filtered))
        return filtered


class RetrievalService:
    """Orchestrates retrieval: hybrid search → rerank → score filter."""

    def __init__(
        self,
        hybrid_search: HybridSearch,
        reranker: CohereReranker,
        score_filter: ScoreFilter,
    ) -> None:
        self._hybrid_search = hybrid_search
        self._reranker = reranker
        self._score_filter = score_filter

    def retrieve(self, query: str, metadata_filter: MetadataFilter | None = None) -> list[RetrievedChunk]:
        candidates = self._hybrid_search.search(query, metadata_filter=metadata_filter)
        candidates = self._reranker.rerank(query, candidates)
        candidates = self._score_filter.filter(candidates)
        return candidates
