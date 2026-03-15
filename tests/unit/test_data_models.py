from data_pipeline.models import ChunkData, ChunkedDocument, RawDocument


def test_raw_document_fields():
    doc = RawDocument(source_file="1.txt", content="hello")
    assert doc.source_file == "1.txt"
    assert doc.content == "hello"


def test_chunk_data_defaults():
    chunk = ChunkData(content="text", content_for_llm="more text")
    assert chunk.embedding == []


def test_chunk_data_with_embedding():
    chunk = ChunkData(content="text", content_for_llm="more", embedding=[0.1, 0.2])
    assert chunk.embedding == [0.1, 0.2]


def test_chunked_document_defaults():
    doc = ChunkedDocument(source_file="1.txt", content="full text")
    assert doc.year is None
    assert doc.business_segment == "deutsche_telekom_group"
    assert doc.document_type == "general"
    assert doc.chunks == []


def test_chunked_document_with_metadata():
    doc = ChunkedDocument(
        source_file="1.txt",
        content="full text",
        year=2024,
        business_segment="t_mobile_us",
        document_type="financial_report",
        chunks=[ChunkData(content="chunk1", content_for_llm="chunk1 context")],
    )
    assert doc.year == 2024
    assert doc.business_segment == "t_mobile_us"
    assert len(doc.chunks) == 1
