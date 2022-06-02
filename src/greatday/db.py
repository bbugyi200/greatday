"""Contains all database utilities."""

from __future__ import annotations

from functools import lru_cache as cache
from typing import Any

from sqlalchemy.future import Engine
from sqlmodel import SQLModel, create_engine


@cache
def cached_engine(url: str, **kwargs: Any) -> Engine:
    """Helper function for creating a new (if necessary) sqlalchemy engine."""
    engine = create_engine(url, **kwargs)
    SQLModel.metadata.create_all(engine)
    return engine
