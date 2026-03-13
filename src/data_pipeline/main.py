import asyncio
import logging

from data_pipeline.pipeline import Pipeline
from data_pipeline.steps import CleanerStep, EmbedderStep, IndexerStep, LLMChunkerStep, LoaderStep, RaptorStep
from shared.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()

    pipeline = Pipeline(
        steps=[
            LoaderStep(data_dir="data/raw"),
            CleanerStep(),
            LLMChunkerStep(settings),
            EmbedderStep(settings),
            IndexerStep(settings),
            RaptorStep(settings),
        ]
    )

    logger.info("Starting data pipeline")
    ctx = await pipeline.run()
    logger.info(
        "Pipeline complete — processed %d documents, %d chunks",
        len(ctx.raw_documents),
        sum(len(d.get("chunks", [])) for d in ctx.raw_documents),
    )


if __name__ == "__main__":
    asyncio.run(main())
