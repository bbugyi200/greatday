"""Contains all database utilities."""

from __future__ import annotations

from functools import lru_cache as cache
import os
from typing import Any

from sqlalchemy.future import Engine
from sqlmodel import SQLModel, create_engine as sqlmodel_create_engine


@cache
def create_cached_engine(url: str, /, **kwargs: Any) -> Engine:
    """Helper function for creating a new (if necessary) sqlalchemy engine."""
    engine = create_engine(url, **kwargs)
    return engine


def create_engine(url: str, /, **kwargs: Any) -> Engine:
    """Wrapper around sqlmodel.create_engine() that makes sure tables exist."""
    if "echo" not in kwargs and "ECHO_SQL_QUERIES" in os.environ:
        kwargs["echo"] = True

    engine = sqlmodel_create_engine(url, **kwargs)
    SQLModel.metadata.create_all(engine)
    return engine
