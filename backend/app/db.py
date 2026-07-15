from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    return _engine


@contextmanager
def begin() -> Iterator:
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def execute(sql: str, **params):
    with begin() as conn:
        return conn.execute(text(sql), params)
