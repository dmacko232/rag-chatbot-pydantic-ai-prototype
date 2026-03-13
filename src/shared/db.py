import sqlite3
from pathlib import Path

import sqlite_vec
from sqlmodel import Session, SQLModel, create_engine

from shared.config import Settings


def _enable_vec_extension(dbapi_conn: sqlite3.Connection, _connection_record: object) -> None:
    dbapi_conn.enable_load_extension(True)
    sqlite_vec.load(dbapi_conn)
    dbapi_conn.enable_load_extension(False)


def create_db_engine(settings: Settings):
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    from sqlalchemy import event

    event.listen(engine, "connect", _enable_vec_extension)
    return engine


def init_db(settings: Settings):
    engine = create_db_engine(settings)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vec0(
                chunk_id INTEGER PRIMARY KEY,
                embedding FLOAT[1024]
            )
            """
        )
        session.commit()

    return engine
