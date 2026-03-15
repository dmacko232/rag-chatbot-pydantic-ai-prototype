from dataclasses import dataclass, field


@dataclass
class ChunkData:
    content: str
    content_for_llm: str
    embedding: list[float] = field(default_factory=list)


@dataclass
class RawDocument:
    source_file: str
    content: str


@dataclass
class ChunkedDocument:
    source_file: str
    content: str
    year: int | None = None
    business_segment: str = "deutsche_telekom_group"
    document_type: str = "general"
    chunks: list[ChunkData] = field(default_factory=list)
