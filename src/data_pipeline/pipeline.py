import logging

from data_pipeline.interfaces import (
    IChunkEmbedder,
    IDocumentChunker,
    IDocumentCleaner,
    IDocumentIndexer,
    IDocumentLoader,
    IRaptorSummarizer,
)
from data_pipeline.models import ChunkedDocument

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(
        self,
        loader: IDocumentLoader,
        cleaner: IDocumentCleaner,
        chunker: IDocumentChunker,
        embedder: IChunkEmbedder,
        indexer: IDocumentIndexer,
        raptor: IRaptorSummarizer | None = None,
    ) -> None:
        self._loader = loader
        self._cleaner = cleaner
        self._chunker = chunker
        self._embedder = embedder
        self._indexer = indexer
        self._raptor = raptor

    async def run(self) -> list[ChunkedDocument]:
        logger.info("Loading documents")
        raw_docs = await self._loader.load()
        logger.info("Loaded %d documents", len(raw_docs))

        logger.info("Cleaning documents")
        raw_docs = await self._cleaner.clean(raw_docs)

        logger.info("Chunking documents")
        chunked_docs = await self._chunker.chunk(raw_docs)
        total_chunks = sum(len(d.chunks) for d in chunked_docs)
        logger.info("Created %d chunks from %d documents", total_chunks, len(chunked_docs))

        logger.info("Embedding chunks")
        chunked_docs = await self._embedder.embed(chunked_docs)

        logger.info("Indexing to database")
        await self._indexer.index(chunked_docs)

        if self._raptor:
            logger.info("Generating RAPTOR summaries")
            await self._raptor.summarize(raw_docs)

        logger.info("Pipeline complete")
        return chunked_docs
