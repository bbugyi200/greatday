"""Contains greatday's SQL model class definitions."""

# WARNING: Don't bother importing __future__.annotations in this module!
import datetime as dt
from typing import List, Optional

from sqlmodel import Column, Field, Relationship, SQLModel, String
from sqlmodel.sql.expression import Select, SelectOfScalar


# HACK: see https://github.com/tiangolo/sqlmodel/issues/189
Select.inherit_cache = True  # type: ignore[attr-defined]
SelectOfScalar.inherit_cache = True  # type: ignore[attr-defined]


###############################################################################
# abstract model classes
###############################################################################
class Base(SQLModel):
    """Abstract base model class."""

    id: Optional[int] = Field(default=None, primary_key=True)


class TodoLink(SQLModel):
    """Abstract model for association/link models."""

    todo_id: Optional[int] = Field(
        default=None, foreign_key="todo.id", primary_key=True
    )


class Tag(Base):
    """Abstract model class for todo.txt tags."""

    name: str = Field(sa_column=Column(String, unique=True))


###############################################################################
# link models (i.e. assocation tables for many-to-many relationships)
###############################################################################
class ProjectLink(TodoLink, table=True):
    """Association model for todos-to-projects relationships."""

    project_id: Optional[int] = Field(
        default=None, foreign_key="project.id", primary_key=True
    )


class ContextLink(TodoLink, table=True):
    """Association model for todos-to-contexts relationships."""

    context_id: Optional[int] = Field(
        default=None, foreign_key="context.id", primary_key=True
    )


class EpicLink(TodoLink, table=True):
    """Association model for todos-to-epics relationships."""

    epic_id: Optional[int] = Field(
        default=None, foreign_key="epic.id", primary_key=True
    )


class MetatagLink(TodoLink, table=True):
    """Association model for todos-to-metatags relationships."""

    metatag_id: Optional[int] = Field(
        default=None, foreign_key="metatag.id", primary_key=True
    )

    todo: "Todo" = Relationship(back_populates="metatag_links")
    metatag: "Metatag" = Relationship(back_populates="links")

    value: str


###############################################################################
# model used to store todos
###############################################################################
class Todo(Base, table=True):
    """Model class for greatday Todos."""

    # table columns
    create_date: dt.date
    desc: str
    done: bool
    done_date: Optional[dt.date]
    priority: str

    # relationships
    contexts: List["Context"] = Relationship(
        back_populates="todos", link_model=ContextLink
    )
    epics: List["Epic"] = Relationship(
        back_populates="todos", link_model=EpicLink
    )
    projects: List["Project"] = Relationship(
        back_populates="todos", link_model=ProjectLink
    )
    metatag_links: List["MetatagLink"] = Relationship(back_populates="todo")


###############################################################################
# tag models
###############################################################################
class Project(Tag, table=True):
    """Model class for todo.txt project tags (e.g. +greatday)."""

    todos: List[Todo] = Relationship(
        back_populates="projects", link_model=ProjectLink
    )


class Context(Tag, table=True):
    """Model class for todo.txt context tags (e.g. @home)."""

    todos: List[Todo] = Relationship(
        back_populates="contexts", link_model=ContextLink
    )


class Epic(Tag, table=True):
    """Model class for (magodo extended) todo.txt epic tags (e.g. #gtd)."""

    todos: List[Todo] = Relationship(
        back_populates="epics", link_model=EpicLink
    )


class Metatag(Tag, table=True):
    """Model class for metadata tags (e.g. due:2022-06-01)."""

    links: List[MetatagLink] = Relationship(back_populates="metatag")
