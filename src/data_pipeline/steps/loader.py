import logging
from pathlib import Path

from data_pipeline.interfaces import IDocumentLoader
from data_pipeline.models import RawDocument

logger = logging.getLogger(__name__)


class FileDocumentLoader(IDocumentLoader):
    def __init__(self, data_dir: str = "data/raw") -> None:
        self._data_dir = Path(data_dir)

    async def load(self) -> list[RawDocument]:
        files = sorted(self._data_dir.glob("*.txt"), key=lambda p: int(p.stem))
        logger.info("Found %d files in %s", len(files), self._data_dir)
        return [
            RawDocument(source_file=f.name, content=f.read_text(encoding="utf-8"))
            for f in files
        ]
