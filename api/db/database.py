from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if config.DATABASE_URL.startswith("sqlite")
    else {},
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_sqlite_columns():
    if not config.DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "detections" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("detections")}
    additions = {
        "content_hash": "VARCHAR(64)",
        "latency_ms": "FLOAT",
        "cached": "BOOLEAN DEFAULT 0",
        "tenant_id": "INTEGER DEFAULT 0",
        "emotion": "VARCHAR(32)",
        "emotion_confidence": "FLOAT",
    }
    with engine.begin() as conn:
        for col, col_type in additions.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE detections ADD COLUMN {col} {col_type}"))


def init_db():
    from db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_columns()
