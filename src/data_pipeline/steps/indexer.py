import json
import logging
import struct

from sqlmodel import Session

from data_pipeline.pipeline import PipelineContext, Step
from shared.config import Settings
from shared.db import init_db
from shared.models import Chunk, Document

logger = logging.getLogger(__name__)


def _serialize_f32(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


class IndexerStep(Step):
    """Persist documents, chunks, and embeddings to SQLite."""

    def __init__(self, settings: Settings) -> None:
        self._engine = init_db(settings)

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        with Session(self._engine) as session:
            for raw_doc in ctx.raw_documents:
                doc = Document(
                    source_file=raw_doc["source_file"],
                    content=raw_doc["content"],
                    year=raw_doc.get("year"),
                    business_segment=raw_doc.get("business_segment"),
                    document_type=raw_doc.get("document_type"),
                )
                session.add(doc)
                session.flush()

                for i, raw_chunk in enumerate(raw_doc.get("chunks", [])):
                    chunk = Chunk(
                        document_id=doc.id,
                        content=raw_chunk["content"],
                        content_for_llm=raw_chunk.get("content_for_llm", raw_chunk["content"]),
                        chunk_index=i,
                    )
                    session.add(chunk)
                    session.flush()

                    embedding = raw_chunk.get("embedding")
                    if embedding:
                        session.execute(
                            "INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (:cid, :emb)",
                            {"cid": chunk.id, "emb": _serialize_f32(embedding)},
                        )

            session.commit()
            doc_count = session.query(Document).count()
            chunk_count = session.query(Chunk).count()
            logger.info("Indexed %d documents, %d chunks", doc_count, chunk_count)

        return ctx
