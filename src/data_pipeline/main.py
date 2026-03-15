import asyncio
import logging

from data_pipeline.interfaces import IDocumentChunker
from data_pipeline.pipeline import DataPipeline
from data_pipeline.steps import (
    CohereChunkEmbedder,
    FileDocumentLoader,
    FixedSizeChunker,
    LLMDocumentChunker,
    LLMRaptorSummarizer,
    RegexDocumentCleaner,
    SQLiteDocumentIndexer,
)
from shared.config import get_settings
from shared.prompts import get_config_section

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _build_chunker(settings) -> IDocumentChunker:
    cfg = get_config_section("chunking")
    strategy = cfg.get("strategy", "fixed")

    if strategy == "llm":
        concurrency = cfg.get("llm_concurrency", 5)
        logger.info("Using LLM chunker (concurrency=%d)", concurrency)
        return LLMDocumentChunker(settings, concurrency=concurrency)

    logger.info("Using fixed-size chunker (size=%d, overlap=%d)", cfg["chunk_size"], cfg["overlap"])
    return FixedSizeChunker(chunk_size=cfg["chunk_size"], overlap=cfg["overlap"])


async def main() -> None:
    settings = get_settings()

    raptor_cfg = get_config_section("raptor")
    raptor = LLMRaptorSummarizer(settings) if raptor_cfg.get("enabled", False) else None
    if raptor:
        logger.info("RAPTOR enabled")
    else:
        logger.info("RAPTOR disabled")

    pipeline = DataPipeline(
        loader=FileDocumentLoader(data_dir="data/raw"),
        cleaner=RegexDocumentCleaner(),
        chunker=_build_chunker(settings),
        embedder=CohereChunkEmbedder(settings),
        indexer=SQLiteDocumentIndexer(settings),
        raptor=raptor,
    )

    result = await pipeline.run()
    total_chunks = sum(len(d.chunks) for d in result)
    logger.info("Processed %d documents, %d chunks", len(result), total_chunks)


if __name__ == "__main__":
    asyncio.run(main())
