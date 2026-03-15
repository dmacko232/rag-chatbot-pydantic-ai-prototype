import asyncio
import json
import logging
import struct
from collections import defaultdict

import cohere
import numpy as np
from openai import AsyncAzureOpenAI
from sklearn.cluster import KMeans
from sqlalchemy import text
from sqlmodel import Session

from data_pipeline.interfaces import IRaptorSummarizer
from data_pipeline.models import ChunkedDocument
from shared.config import Settings
from shared.db import create_db_engine
from shared.models import Chunk, Document
from shared.prompts import get_config_section, get_prompt

logger = logging.getLogger(__name__)


def _serialize_f32(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


class LLMRaptorSummarizer(IRaptorSummarizer):
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            max_retries=10,
        )
        self._deployment = settings.azure_openai_deployment
        self._cohere = cohere.Client(api_key=settings.cohere_api_key)
        self._embed_model = settings.cohere_embed_model
        self._engine = create_db_engine(settings)

        cfg = get_config_section("raptor")
        self._cluster_size = cfg.get("cluster_size", 10)
        self._max_levels = cfg.get("max_levels", 3)
        self._concurrency = cfg.get("concurrency", 10)

    async def summarize(self, documents: list[ChunkedDocument]) -> None:
        texts = [chunk.content for doc in documents for chunk in doc.chunks]
        embeddings = [chunk.embedding for doc in documents for chunk in doc.chunks]

        if not texts or not all(embeddings):
            logger.warning("No chunks with embeddings available for RAPTOR")
            return

        logger.info("Starting RAPTOR with %d leaf chunks (cluster_size=%d, max_levels=%d)",
                     len(texts), self._cluster_size, self._max_levels)

        all_summaries: list[tuple[str, list[float], int]] = []

        for level in range(1, self._max_levels + 1):
            n_clusters = max(len(texts) // self._cluster_size, 2)
            if n_clusters >= len(texts):
                logger.info("Level %d: only %d texts, fewer than cluster count — stopping", level, len(texts))
                break

            logger.info("Level %d: clustering %d texts into %d clusters", level, len(texts), n_clusters)

            embedding_matrix = np.array(embeddings)
            labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(embedding_matrix)

            clusters: dict[int, list[str]] = defaultdict(list)
            for i, label in enumerate(labels):
                clusters[label].append(texts[i])

            logger.info("Level %d: summarizing %d clusters (concurrency=%d)", level, len(clusters), self._concurrency)
            summaries = await self._summarize_clusters(list(clusters.values()))

            logger.info("Level %d: embedding %d summaries", level, len(summaries))
            new_embeddings = self._embed_texts(summaries)

            for s, e in zip(summaries, new_embeddings):
                all_summaries.append((s, e, level))

            texts = summaries
            embeddings = new_embeddings

            if len(texts) <= self._cluster_size:
                logger.info("Level %d produced %d texts — stopping recursion", level, len(texts))
                break

        if all_summaries:
            self._store_summaries(all_summaries)
            logger.info("RAPTOR complete: %d summaries across %d levels",
                         len(all_summaries), max(lvl for _, _, lvl in all_summaries))
        else:
            logger.warning("RAPTOR produced no summaries")

    async def _summarize_clusters(self, clusters: list[list[str]]) -> list[str]:
        semaphore = asyncio.Semaphore(self._concurrency)
        system_prompt = get_prompt("raptor_system_prompt")

        async def _summarize_one(cluster_texts: list[str]) -> str:
            combined = "\n\n---\n\n".join(cluster_texts)
            async with semaphore:
                response = await self._client.chat.completions.create(
                    model=self._deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": combined},
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )

            raw = response.choices[0].message.content or '{"summary": ""}'
            try:
                parsed = json.loads(raw)
                return parsed.get("summary", raw)
            except json.JSONDecodeError:
                return raw

        results = await asyncio.gather(*[_summarize_one(c) for c in clusters])
        return [r for r in results if r.strip()]

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self._cohere.embed(
            texts=texts, model=self._embed_model, input_type="search_document"
        )
        return response.embeddings

    def _store_summaries(self, summaries: list[tuple[str, list[float], int]]) -> None:
        with Session(self._engine) as session:
            raptor_doc = Document(
                source_file="_raptor_summaries",
                content="RAPTOR hierarchical summaries",
                document_type="general",
            )
            session.add(raptor_doc)
            session.flush()

            for i, (content, embedding, level) in enumerate(summaries):
                chunk = Chunk(
                    document_id=raptor_doc.id,
                    content=content,
                    content_for_llm=content,
                    chunk_index=i,
                    is_raptor_summary=True,
                )
                session.add(chunk)
                session.flush()

                session.execute(
                    text("INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (:cid, :emb)"),
                    {"cid": chunk.id, "emb": _serialize_f32(embedding)},
                )
                session.execute(
                    text("INSERT INTO chunk_fts (rowid, content) VALUES (:cid, :content)"),
                    {"cid": chunk.id, "content": content},
                )

            session.commit()
            level_counts = defaultdict(int)
            for _, _, lvl in summaries:
                level_counts[lvl] += 1
            breakdown = ", ".join(f"L{k}={v}" for k, v in sorted(level_counts.items()))
            logger.info("Indexed %d RAPTOR summaries (%s)", len(summaries), breakdown)
