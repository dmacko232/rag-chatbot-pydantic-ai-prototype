import pytest

from data_pipeline.steps.chunker import FixedSizeChunker
from data_pipeline.models import RawDocument


@pytest.fixture
def chunker():
    return FixedSizeChunker(chunk_size=100, overlap=20)


@pytest.mark.asyncio
async def test_short_doc_single_chunk(chunker):
    docs = [RawDocument(source_file="1.txt", content="Short text.")]
    result = await chunker.chunk(docs)
    assert len(result) == 1
    assert len(result[0].chunks) == 1
    assert result[0].chunks[0].content == "Short text."


@pytest.mark.asyncio
async def test_splits_long_doc(chunker):
    text = "A" * 250
    docs = [RawDocument(source_file="1.txt", content=text)]
    result = await chunker.chunk(docs)
    assert len(result[0].chunks) > 1


@pytest.mark.asyncio
async def test_overlap_in_content(chunker):
    text = "A" * 200
    docs = [RawDocument(source_file="1.txt", content=text)]
    result = await chunker.chunk(docs)
    chunks = result[0].chunks
    assert len(chunks) == 3
    assert len(chunks[0].content) == 100
    assert len(chunks[1].content) == 100


@pytest.mark.asyncio
async def test_context_is_larger_than_content(chunker):
    text = "A" * 250
    docs = [RawDocument(source_file="1.txt", content=text)]
    result = await chunker.chunk(docs)
    for chunk in result[0].chunks:
        assert len(chunk.content_for_llm) >= len(chunk.content)


@pytest.mark.asyncio
async def test_empty_document():
    chunker = FixedSizeChunker(chunk_size=100, overlap=20)
    docs = [RawDocument(source_file="1.txt", content="")]
    result = await chunker.chunk(docs)
    assert len(result) == 1
    assert result[0].chunks == []


@pytest.mark.asyncio
async def test_preserves_source_file(chunker):
    docs = [RawDocument(source_file="42.txt", content="Hello world")]
    result = await chunker.chunk(docs)
    assert result[0].source_file == "42.txt"


@pytest.mark.asyncio
async def test_multiple_documents(chunker):
    docs = [
        RawDocument(source_file="1.txt", content="Doc one"),
        RawDocument(source_file="2.txt", content="Doc two" * 50),
    ]
    result = await chunker.chunk(docs)
    assert len(result) == 2
    assert len(result[0].chunks) == 1
    assert len(result[1].chunks) > 1
