import pytest

from data_pipeline.interfaces import (
    IChunkEmbedder,
    IDocumentChunker,
    IDocumentCleaner,
    IDocumentIndexer,
    IDocumentLoader,
    IRaptorSummarizer,
)
from data_pipeline.models import ChunkData, ChunkedDocument, RawDocument
from data_pipeline.pipeline import DataPipeline


class FakeLoader(IDocumentLoader):
    def __init__(self, docs: list[RawDocument]) -> None:
        self._docs = docs

    async def load(self) -> list[RawDocument]:
        return self._docs


class FakeCleaner(IDocumentCleaner):
    async def clean(self, documents: list[RawDocument]) -> list[RawDocument]:
        return [RawDocument(source_file=d.source_file, content=d.content.strip()) for d in documents]


class FakeChunker(IDocumentChunker):
    async def chunk(self, documents: list[RawDocument]) -> list[ChunkedDocument]:
        return [
            ChunkedDocument(
                source_file=d.source_file,
                content=d.content,
                chunks=[ChunkData(content=d.content, content_for_llm=d.content)],
            )
            for d in documents
        ]


class FakeEmbedder(IChunkEmbedder):
    async def embed(self, documents: list[ChunkedDocument]) -> list[ChunkedDocument]:
        for doc in documents:
            for chunk in doc.chunks:
                chunk.embedding = [0.1, 0.2, 0.3]
        return documents


class FakeIndexer(IDocumentIndexer):
    def __init__(self) -> None:
        self.indexed: list[ChunkedDocument] = []

    async def index(self, documents: list[ChunkedDocument]) -> None:
        self.indexed.extend(documents)


class FakeRaptor(IRaptorSummarizer):
    def __init__(self) -> None:
        self.called = False

    async def summarize(self, documents: list[RawDocument]) -> None:
        self.called = True


@pytest.mark.asyncio
async def test_pipeline_runs_all_steps():
    raw_docs = [RawDocument(source_file="1.txt", content="Hello world")]
    indexer = FakeIndexer()

    pipeline = DataPipeline(
        loader=FakeLoader(raw_docs),
        cleaner=FakeCleaner(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        indexer=indexer,
    )

    result = await pipeline.run()

    assert len(result) == 1
    assert result[0].source_file == "1.txt"
    assert len(result[0].chunks) == 1
    assert result[0].chunks[0].embedding == [0.1, 0.2, 0.3]
    assert len(indexer.indexed) == 1


@pytest.mark.asyncio
async def test_pipeline_with_raptor():
    raw_docs = [RawDocument(source_file="1.txt", content="Hello")]
    raptor = FakeRaptor()

    pipeline = DataPipeline(
        loader=FakeLoader(raw_docs),
        cleaner=FakeCleaner(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        indexer=FakeIndexer(),
        raptor=raptor,
    )

    await pipeline.run()
    assert raptor.called


@pytest.mark.asyncio
async def test_pipeline_without_raptor():
    pipeline = DataPipeline(
        loader=FakeLoader([RawDocument(source_file="1.txt", content="Hello")]),
        cleaner=FakeCleaner(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        indexer=FakeIndexer(),
        raptor=None,
    )

    result = await pipeline.run()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_pipeline_empty_input():
    indexer = FakeIndexer()

    pipeline = DataPipeline(
        loader=FakeLoader([]),
        cleaner=FakeCleaner(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        indexer=indexer,
    )

    result = await pipeline.run()
    assert result == []
    assert indexer.indexed == []


@pytest.mark.asyncio
async def test_pipeline_multiple_documents():
    raw_docs = [
        RawDocument(source_file="1.txt", content="Doc one"),
        RawDocument(source_file="2.txt", content="Doc two"),
        RawDocument(source_file="3.txt", content="Doc three"),
    ]
    indexer = FakeIndexer()

    pipeline = DataPipeline(
        loader=FakeLoader(raw_docs),
        cleaner=FakeCleaner(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        indexer=indexer,
    )

    result = await pipeline.run()
    assert len(result) == 3
    assert len(indexer.indexed) == 3
    source_files = {d.source_file for d in result}
    assert source_files == {"1.txt", "2.txt", "3.txt"}
