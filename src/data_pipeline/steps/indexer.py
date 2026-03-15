import logging
import struct

from sqlalchemy import text
from sqlmodel import Session

from data_pipeline.interfaces import IDocumentIndexer
from data_pipeline.models import ChunkedDocument
from shared.config import Settings
from shared.db import init_db
from shared.models import Chunk, Document

logger = logging.getLogger(__name__)


def _serialize_f32(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


class SQLiteDocumentIndexer(IDocumentIndexer):
    def __init__(self, settings: Settings) -> None:
        self._engine = init_db(settings)

    async def index(self, documents: list[ChunkedDocument]) -> None:
        with Session(self._engine) as session:
            for chunked_doc in documents:
                doc = Document(
                    source_file=chunked_doc.source_file,
                    content=chunked_doc.content,
                    year=chunked_doc.year,
                    business_segment=chunked_doc.business_segment,
                    document_type=chunked_doc.document_type,
                )
                session.add(doc)
                session.flush()

                for i, chunk_data in enumerate(chunked_doc.chunks):
                    chunk = Chunk(
                        document_id=doc.id,
                        content=chunk_data.content,
                        content_for_llm=chunk_data.content_for_llm,
                        chunk_index=i,
                    )
                    session.add(chunk)
                    session.flush()

                    session.execute(
                        text("INSERT INTO chunk_fts (rowid, content) VALUES (:cid, :content)"),
                        {"cid": chunk.id, "content": chunk_data.content},
                    )

                    if chunk_data.embedding:
                        session.execute(
                            text("INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (:cid, :emb)"),
                            {"cid": chunk.id, "emb": _serialize_f32(chunk_data.embedding)},
                        )

            session.commit()
            doc_count = session.query(Document).count()
            chunk_count = session.query(Chunk).count()
            logger.info("Indexed %d documents, %d chunks", doc_count, chunk_count)
