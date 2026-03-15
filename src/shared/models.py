from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from shared.config import BusinessSegment, DocumentType


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_file: str = Field(index=True)
    content: str
    year: int | None = Field(default=None, index=True)
    business_segment: BusinessSegment | None = Field(default=None, index=True)
    document_type: DocumentType | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    chunks: list["Chunk"] = Relationship(back_populates="document")


class Chunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    content: str
    content_for_llm: str
    chunk_index: int
    is_raptor_summary: bool = Field(default=False)

    document: Document | None = Relationship(back_populates="chunks")
