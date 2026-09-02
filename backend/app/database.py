"""SQLite engine/session setup via SQLAlchemy."""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# Ensure the sqlite file's parent directory exists (e.g. ./data/reports.db)
if settings.database_url.startswith("sqlite:///./"):
    rel_path = settings.database_url.replace("sqlite:///./", "", 1)
    parent = os.path.dirname(rel_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they're registered on Base.metadata before create_all
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
