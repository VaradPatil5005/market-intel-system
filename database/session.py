"""
Database session management and a lightweight repository layer.

Keeps persistence code (session lifecycle, CRUD, bulk save) reusable
across agents/orchestration without leaking SQLAlchemy details into
business logic.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base
from utils.config import settings

ModelT = TypeVar("ModelT", bound=Base)

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Repository:
    """Generic CRUD + bulk-save helper for any ORM model."""

    def __init__(self, model: Type[ModelT]):
        self.model = model

    def insert(self, session: Session, obj: ModelT) -> ModelT:
        session.add(obj)
        session.flush()
        return obj

    def bulk_insert(self, session: Session, objs: Iterable[ModelT]) -> List[ModelT]:
        objs = list(objs)
        session.add_all(objs)
        session.flush()
        return objs

    def get(self, session: Session, id_: str) -> ModelT | None:
        return session.get(self.model, id_)

    def all(self, session: Session, limit: int | None = None) -> List[ModelT]:
        query = session.query(self.model)
        if limit:
            query = query.limit(limit)
        return query.all()

    def filter_by(self, session: Session, **kwargs: Any) -> List[ModelT]:
        return session.query(self.model).filter_by(**kwargs).all()

    def update(self, session: Session, id_: str, **fields: Any) -> ModelT | None:
        obj = self.get(session, id_)
        if obj is None:
            return None
        for key, value in fields.items():
            setattr(obj, key, value)
        session.flush()
        return obj

    def delete(self, session: Session, id_: str) -> bool:
        obj = self.get(session, id_)
        if obj is None:
            return False
        session.delete(obj)
        session.flush()
        return True

    def to_dicts(self, objs: Iterable[ModelT]) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in objs]  # type: ignore[attr-defined]
