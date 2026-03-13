import logging
from pathlib import Path

from data_pipeline.pipeline import PipelineContext, Step

logger = logging.getLogger(__name__)


class LoaderStep(Step):
    """Load raw text files from a local directory."""

    def __init__(self, data_dir: str = "data/raw") -> None:
        self._data_dir = Path(data_dir)

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        files = sorted(self._data_dir.glob("*.txt"), key=lambda p: int(p.stem))
        logger.info("Found %d files in %s", len(files), self._data_dir)

        for file_path in files:
            content = file_path.read_text(encoding="utf-8")
            ctx.raw_documents.append({"source_file": file_path.name, "content": content})

        return ctx
