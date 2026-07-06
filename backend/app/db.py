"""Database engine, session factory, and declarative base.

Shared by every persistence feature. Roadmap features (#3 consumption tracking, #4
suggestions) add their own model modules under ``app/models/`` and reuse ``get_db`` /
``Base`` from here — no changes needed in this file.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# check_same_thread is a SQLite-only quirk; harmless to omit for other backends.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base every ORM model inherits from."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for all registered models. Called once on startup."""
    from app import models  # noqa: F401 - import registers models on Base.metadata

    Base.metadata.create_all(bind=engine)
