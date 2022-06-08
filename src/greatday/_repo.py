"""Contains the Repo class."""

from __future__ import annotations

from dataclasses import dataclass
import operator
from pathlib import Path
from typing import Any, Callable, TypeVar

from eris import ErisResult, Err, Ok
from logrus import Logger
import magodo
from potoroo import Repo, TaggedRepo
from sqlalchemy import func
from sqlmodel import Integer, Session, or_, select
from sqlmodel.sql.expression import SelectOfScalar
from typist import PathLike

from . import db, models
from ._common import NULL_ID
from ._tag import (
    DescOperator,
    GreatTag,
    MetatagOperator,
    MetatagValueType,
    Tag,
)
from ._todo import GreatTodo
from .types import CreateEngineType


logger = Logger(__name__)

SelectOfTodo = SelectOfScalar[models.Todo]
SQLStatementParser = Callable[["SQLTag", SelectOfTodo], SelectOfTodo]
T = TypeVar("T")

# will be populated by the @sql_stmt_parser decorator
SQL_STMT_PARSERS: list[SQLStatementParser] = []


def sql_stmt_parser(parser: SQLStatementParser) -> SQLStatementParser:
    """Decorator that registers statement parsers for SQLTag class."""
    SQL_STMT_PARSERS.append(parser)
    return parser


class SQLRepo(TaggedRepo[str, GreatTodo, GreatTag]):
    """Repo that stores Todos in sqlite database."""

    def __init__(
        self,
        url: str,
        *,
        engine_factory: CreateEngineType = db.create_cached_engine,
        verbose: int = 0,
    ) -> None:
        self.url = url

        # create the Engine object
        kwargs = {}
        if verbose > 2:
            kwargs["echo"] = True
        self.engine = engine_factory(url, **kwargs)

    def add(self, todo: GreatTodo, /, *, key: str = None) -> ErisResult[str]:
        """Adds a new Todo to the DB.

        Returns a unique identifier that has been associated with this Todo.
        """
        with Session(self.engine) as session:
            mtodo = todo.to_model(session, key=key)
            session.add(mtodo)
            session.commit()
            session.refresh(mtodo)

        return Ok(str(mtodo.id))

    def get(self, key: str) -> ErisResult[GreatTodo | None]:
        """Retrieve a Todo from the DB."""
        with Session(self.engine) as session:
            stmt = select(models.Todo).where(models.Todo.id == int(key))
            results = session.exec(stmt)
            mtodo = results.first()
            if mtodo is None:
                return Ok(None)
            else:
                todo = GreatTodo.from_model(mtodo)
                return Ok(todo)

    def remove(self, key: str) -> ErisResult[GreatTodo | None]:
        """Remove a Todo from the DB."""
        with Session(self.engine) as session:
            stmt = select(models.Todo).where(models.Todo.id == int(key))
            results = session.exec(stmt)
            mtodo = results.first()
            if mtodo is None:
                return Ok(None)
            else:
                todo = GreatTodo.from_model(mtodo)

                for mlink in mtodo.metatag_links:
                    delete_metatag = len(mlink.metatag.links) == 1
                    session.delete(mlink)
                    if delete_metatag:
                        session.delete(mlink.metatag)
                    session.commit()

                for mtodo_tags in [
                    mtodo.contexts,
                    mtodo.epics,
                    mtodo.projects,
                ]:
                    for tag in mtodo_tags:  # type: ignore[attr-defined]
                        if len(tag.todos) == 1:
                            session.delete(tag)
                            session.commit()

                session.delete(mtodo)
                session.commit()
                return Ok(todo)

    def get_by_tag(self, tag: GreatTag) -> ErisResult[list[GreatTodo]]:
        """Get Todo(s) from DB by using a tag."""
        todos: list[GreatTodo] = []
        found_mtodo_ids: set[int] = set()
        with Session(self.engine) as session:
            for child_tag in tag.tags:
                stmt = SQLTag(session, child_tag).to_stmt()

                for mtodo in session.exec(stmt).all():
                    if mtodo.id not in found_mtodo_ids:
                        assert mtodo.id is not None, (
                            "All of these Todo models are being pulled from a"
                            " SELECT statement, so they should already have an"
                            " 'id' field."
                        )
                        found_mtodo_ids.add(mtodo.id)
                        todo = GreatTodo.from_model(mtodo)
                        todos.append(todo)
        return Ok(todos)

    def remove_by_tag(self, tag: GreatTag) -> ErisResult[list[GreatTodo]]:
        """Removes Todo(s) from DB by using a tag."""
        removed_todos = self.get_by_tag(tag).unwrap()
        for todo in removed_todos:
            self.remove(todo.ident).unwrap()
        return Ok(removed_todos)

    def all(self) -> ErisResult[list[GreatTodo]]:
        """Returns all Todos contained in the underlying SQL database."""
        todos = []
        with Session(self.engine) as session:
            stmt = select(models.Todo)
            results = session.exec(stmt)
            for mtodo in results.all():
                todo = GreatTodo.from_model(mtodo)
                todos.append(todo)
        return Ok(todos)


@dataclass(frozen=True)
class SQLTag:
    """Wrapper around Tag objects that helps build SQL statements."""

    session: Session
    tag: Tag

    def to_stmt(self) -> SelectOfTodo:
        """Constructs a SQL statement from the provided Tag object."""
        stmt = select(models.Todo)
        for parse_stmt in SQL_STMT_PARSERS:
            stmt = parse_stmt(self, stmt)
        return stmt

    @sql_stmt_parser
    def done_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for done status (i.e. 'x' or 'o')."""
        if self.tag.done is not None:
            stmt = stmt.where(models.Todo.done == self.tag.done)
        return stmt

    @sql_stmt_parser
    def prefix_tag_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for prefix tags (e.g. '@home' or '+greatday')."""
        for prefix_tag_list, link_model, model in [
            (self.tag.contexts, models.ContextLink, models.Context),
            (self.tag.epics, models.EpicLink, models.Epic),
            (self.tag.projects, models.ProjectLink, models.Project),
        ]:
            for prefix_tag in prefix_tag_list:
                if prefix_tag.startswith("-"):
                    name = prefix_tag[1:]
                    op = models.Todo.id.not_in  # type: ignore[union-attr]
                else:
                    name = prefix_tag
                    op = models.Todo.id.in_  # type: ignore[union-attr]

                subquery = (
                    select(models.Todo.id)
                    .join(link_model)
                    .join(model)
                    .where(model.name == name)
                )
                stmt = stmt.where(op(subquery))
        return stmt

    @sql_stmt_parser
    def priority_range_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for priority range (e.g. '(a-c)')."""
        if self.tag.priorities:
            stmt = stmt.where(
                or_(models.Todo.priority == p for p in self.tag.priorities)
            )
        return stmt

    @sql_stmt_parser
    def desc_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for todo description (e.g. '"foo"' or '!"bar"')"""
        for desc_filter in self.tag.desc_filters:
            case_sensitive = desc_filter.case_sensitive
            if case_sensitive is None:
                case_sensitive = not bool(desc_filter.value.islower())

            like_arg = f"%{desc_filter.value}%"
            op_arg: Any
            if case_sensitive:
                cond = models.Todo.desc.like(like_arg)  # type: ignore[attr-defined]
                subquery = select(models.Todo.id, models.Todo.desc).where(cond)
                id_list: list[int] = []
                for ID, desc in self.session.exec(subquery).all():
                    assert (
                        ID is not None
                    ), "The DB shouldn't contain todos without an ID, right?"
                    if desc_filter.value in desc:
                        id_list.append(ID)
                op_map: dict[DescOperator, Any] = {
                    DescOperator.CONTAINS: models.Todo.id.in_,  # type: ignore[union-attr]
                    DescOperator.NOT_CONTAINS: models.Todo.id.not_in,  # type: ignore[union-attr]
                }
                op = op_map[desc_filter.op]
                op_arg = id_list
            else:
                op_map = {
                    DescOperator.CONTAINS: models.Todo.desc.ilike,  # type: ignore[attr-defined]
                    DescOperator.NOT_CONTAINS: models.Todo.desc.not_ilike,  # type: ignore[attr-defined]
                }
                op = op_map[desc_filter.op]
                op_arg = like_arg

            stmt = stmt.where(op(op_arg))
        return stmt

    @sql_stmt_parser
    def date_range_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for create/done dates (e.g. '^2000-01-01' or '$5d:0d')."""
        for date_range_list, model_date in [
            (self.tag.create_date_ranges, models.Todo.create_date),
            (self.tag.done_date_ranges, models.Todo.done_date),
        ]:
            for date_range in date_range_list:
                end_date = date_range.end or date_range.start
                stmt = (
                    stmt.where(model_date is not None)
                    .where(model_date >= date_range.start)  # type: ignore[operator]
                    .where(model_date <= end_date)  # type: ignore[operator]
                )
        return stmt

    @sql_stmt_parser
    def metatag_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for metatags (e.g. 'due<=0d')."""
        comp_op_map = {
            MetatagOperator.EQ: operator.eq,
            MetatagOperator.NE: operator.ne,
            MetatagOperator.LT: operator.lt,
            MetatagOperator.GT: operator.gt,
            MetatagOperator.LE: operator.le,
            MetatagOperator.GE: operator.ge,
        }
        for mfilter in self.tag.metatag_filters:
            if mfilter.key == "id" and mfilter.op not in [
                MetatagOperator.EXISTS,
                MetatagOperator.NOT_EXISTS,
            ]:
                comp_op = comp_op_map[mfilter.op]
                stmt = stmt.where(
                    comp_op(_col_to_int(models.Todo.id), int(mfilter.value))
                )
                continue

            subquery = (
                select(models.Todo.id)
                .join(models.MetatagLink)
                .join(models.Metatag)
                .where(models.Metatag.name == mfilter.key)
            )

            op = models.Todo.id.in_  # type: ignore[union-attr]
            if mfilter.op == MetatagOperator.EXISTS:
                pass
            elif mfilter.op == MetatagOperator.NOT_EXISTS:
                op = models.Todo.id.not_in  # type: ignore[union-attr]
            else:
                comp_op = comp_op_map[mfilter.op]

                value_type_map: dict[
                    MetatagValueType,
                    tuple[Callable[[Any], Any], Callable[[Any], Any]],
                ] = {
                    MetatagValueType.DATE: (func.date, magodo.dates.to_date),
                    MetatagValueType.INTEGER: (_col_to_int, int),
                    MetatagValueType.STRING: (_noop, _noop),
                }
                cast_model, cast_value = value_type_map[mfilter.value_type]
                subquery = subquery.where(
                    comp_op(
                        cast_model(models.MetatagLink.value),
                        cast_value(mfilter.value),
                    )
                )

            stmt = stmt.where(op(subquery))

        return stmt


def _noop(value: T) -> T:
    """A function that does nothing."""
    return value


def _col_to_int(value: Any) -> Any:
    """Casts SQL table's column to integer."""
    return func.cast(value, Integer)


class FileRepo(Repo[str, GreatTodo]):
    """Repo that stores Todos on disk."""

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)

    def add(self, todo: GreatTodo, /, *, key: str = None) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        if key is None:
            assert todo.ident != NULL_ID, (
                "Every todo added to a file should already have an ID assigned"
                " to it."
            )
            key = todo.ident

        all_todos: list[GreatTodo] = [todo]

        if self.path.exists():
            todos = _todos_from_path(self.path)
            all_todos.extend(todos)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w") as f:
            f.write("\n".join(t.to_line() for t in sorted(all_todos)))

        return Ok(key)

    def get(self, key: str) -> ErisResult[GreatTodo | None]:
        """Retrieve a Todo from disk."""
        for line in self.path.read_text().split("\n"):
            if f"id:{key}" in line.strip().split(" "):
                todo = GreatTodo.from_line(line).unwrap()
                return Ok(todo)
        return Ok(None)

    def remove(self, key: str) -> ErisResult[GreatTodo | None]:
        """Remove a Todo from disk."""
        new_lines: list[str] = []

        todo: GreatTodo | None = None
        for line in self.path.read_text().split("\n"):
            for word in line.strip().split(" "):
                if word == f"id:{key}":
                    todo = GreatTodo.from_line(line).unwrap()
                    break
            else:
                new_lines.append(line)

        self.path.write_text("\n".join(new_lines))

        return Ok(todo)

    def all(self) -> ErisResult[list[GreatTodo]]:
        """Retreive all Todos stored on disk."""
        todos = _todos_from_path(self.path)
        return Ok(todos)


def _todos_from_path(path: PathLike) -> list[GreatTodo]:
    path = Path(path)
    todos: list[GreatTodo] = []
    for line in path.read_text().split("\n"):
        todo_result = GreatTodo.from_line(line)
        if not isinstance(todo_result, Err):
            todos.append(todo_result.ok())
    return todos
