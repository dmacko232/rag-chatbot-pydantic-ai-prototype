import logging

import cohere

from data_pipeline.pipeline import PipelineContext, Step
from shared.config import Settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 96


class EmbedderStep(Step):
    """Generate Cohere embeddings for all chunks."""

    def __init__(self, settings: Settings) -> None:
        self._client = cohere.Client(api_key=settings.cohere_api_key)
        self._model = settings.cohere_embed_model

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        all_texts: list[str] = []
        for doc in ctx.raw_documents:
            for chunk in doc.get("chunks", []):
                all_texts.append(chunk["content"])

        logger.info("Embedding %d chunks in batches of %d", len(all_texts), BATCH_SIZE)

        all_embeddings: list[list[float]] = []
        for i in range(0, len(all_texts), BATCH_SIZE):
            batch = all_texts[i : i + BATCH_SIZE]
            response = self._client.embed(
                texts=batch,
                model=self._model,
                input_type="search_document",
            )
            all_embeddings.extend(response.embeddings)

        idx = 0
        for doc in ctx.raw_documents:
            for chunk in doc.get("chunks", []):
                chunk["embedding"] = all_embeddings[idx]
                idx += 1

        return ctx
