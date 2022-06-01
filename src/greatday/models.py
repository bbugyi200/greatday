"""Contains greatday's SQL model class definitions."""

from __future__ import annotations

from sqlmodel import Field, Relationship, SQLModel


class Todo(SQLModel, table=True):
    """Model class for greatday Todos."""

    id: int | None = Field(default=None, primary_key=True)

    projects: list[ProjectTag] = Relationship()


class Tag(SQLModel):
    """Abstract model class for todo.txt tags."""

    id: int | None = Field(default=None, primary_key=True)
    key: str


class ProjectTag(Tag, table=True):
    """Model class for todo.txt project tags (e.g. +greatday)."""


class ContextTag(Tag, table=True):
    """Model class for todo.txt context tags (e.g. @home)."""


class EpicTag(Tag, table=True):
    """Model class for (magodo extended) todo.txt epic tags (e.g. #gtd)."""


class KVTag(Tag, table=True):
    """Model class for metadata tags (e.g. due:2022-06-01)."""
