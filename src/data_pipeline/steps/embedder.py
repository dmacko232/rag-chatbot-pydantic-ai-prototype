import asyncio
import logging

import cohere

from data_pipeline.interfaces import IChunkEmbedder
from data_pipeline.models import ChunkedDocument
from shared.config import Settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 48


class CohereChunkEmbedder(IChunkEmbedder):
    def __init__(self, settings: Settings) -> None:
        self._client = cohere.Client(api_key=settings.cohere_api_key)
        self._model = settings.cohere_embed_model
        self._batch_delay = settings.embed_batch_delay

    async def embed(self, documents: list[ChunkedDocument]) -> list[ChunkedDocument]:
        all_texts: list[str] = []
        for doc in documents:
            for chunk in doc.chunks:
                all_texts.append(chunk.content)

        if not all_texts:
            return documents

        total_batches = (len(all_texts) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info("Embedding %d chunks in %d batches of %d", len(all_texts), total_batches, BATCH_SIZE)

        all_embeddings: list[list[float]] = []
        for i in range(0, len(all_texts), BATCH_SIZE):
            batch_num = i // BATCH_SIZE + 1
            batch = all_texts[i : i + BATCH_SIZE]
            logger.info("Embedding batch %d/%d (%d texts)", batch_num, total_batches, len(batch))

            response = self._client.embed(
                texts=batch,
                model=self._model,
                input_type="search_document",
            )
            all_embeddings.extend(response.embeddings)

            if self._batch_delay > 0 and i + BATCH_SIZE < len(all_texts):
                logger.info("Waiting %.0fs for rate limit...", self._batch_delay)
                await asyncio.sleep(self._batch_delay)

        idx = 0
        for doc in documents:
            for chunk in doc.chunks:
                chunk.embedding = all_embeddings[idx]
                idx += 1

        return documents
