"""Contains the Repo class."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final

from eris import ErisResult, Ok
from logrus import Logger
from magodo import TodoGroup
from potoroo import TaggedRepo
from sqlalchemy.future import Engine
from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar
from typist import PathLike

from . import db, models
from ._dates import init_yyyymm_path
from ._ids import NULL_ID, init_next_todo_id
from ._tag import GreatTag, Tag
from ._todo import GreatTodo


logger = Logger(__name__)

SelectOfTodo = SelectOfScalar[models.Todo]
SQLStatementParser = Callable[["SQLTag", SelectOfTodo], SelectOfTodo]

DEFAULT_TODO_DIR: Final = "todos"

# will be populated by the @sql_stmt_parser decorator
SQL_STMT_PARSERS: list[SQLStatementParser] = []


class SQLRepo(TaggedRepo[str, GreatTodo, GreatTag]):
    """Repo that stores Todos in sqlite database."""

    def __init__(
        self,
        url: str,
        *,
        engine_factory: Callable[[str], Engine] = db.create_cached_engine,
    ) -> None:
        self.url = url
        self.engine = engine_factory(url)

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
                    session.delete(mlink)
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
                stmt = SQLTag(child_tag).to_stmt()

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


def sql_stmt_parser(parser: SQLStatementParser) -> SQLStatementParser:
    """Decorator that registers statement parsers for SQLTag class."""
    SQL_STMT_PARSERS.append(parser)
    return parser


@dataclass(frozen=True)
class SQLTag:
    """Wrapper around Tag objects that helps build SQL statements."""

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
        new_stmt = stmt
        if self.tag.done is not None:
            new_stmt = new_stmt.where(models.Todo.done == self.tag.done)
        return new_stmt

    @sql_stmt_parser
    def prefix_tag_parser(self, stmt: SelectOfTodo) -> SelectOfTodo:
        """Parser for prefix tags (e.g. '@home' or '+greatday')."""
        new_stmt = stmt
        return new_stmt


class FileRepo(TaggedRepo[str, GreatTodo, GreatTag]):
    """Repo that stores Todos on disk."""

    def __init__(self, data_dir: PathLike, path: PathLike = None) -> None:
        self.data_dir = Path(data_dir)
        if path is None:
            self.path = self.data_dir / DEFAULT_TODO_DIR
        else:
            self.path = Path(path)

    @property
    def todo_group(self) -> TodoGroup[GreatTodo]:
        """Returns the TodoGroup associated with this GreatRepo."""
        return TodoGroup.from_path(GreatTodo, self.path)

    def add(self, todo: GreatTodo, /, *, key: str = None) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        drop_old_key = bool(todo.ident == NULL_ID)
        if key is None or key == NULL_ID:
            key = init_next_todo_id(self.data_dir)
        else:
            drop_old_key = True

        mdata = dict(todo.metadata.items())

        old_key = mdata.get("id")
        if (drop_old_key and old_key != key) or not old_key:
            metadata = dict(mdata.items())
            metadata.update({"id": key})
            todo = todo.new(metadata=metadata)

        all_todos: list[GreatTodo] = [todo]

        if self.path.is_dir() or (
            not self.path.exists() and self.path.suffix != ".txt"
        ):
            todo_txt = init_yyyymm_path(self.path, date=todo.create_date)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            todo_txt = self.path

        if todo_txt.exists():
            todo_group = TodoGroup.from_path(GreatTodo, todo_txt)
            all_todos.extend(todo_group)

        with todo_txt.open("w") as f:
            f.write("\n".join(t.to_line() for t in sorted(all_todos)))

        return Ok(key)

    def get(self, key: str) -> ErisResult[GreatTodo | None]:
        """Retrieve a Todo from disk."""
        return Ok(self.todo_group.todo_map.get(key, None))

    def remove(self, key: str) -> ErisResult[GreatTodo | None]:
        """Remove a Todo from disk."""
        todo_txt = self.todo_group.path_map[key]

        new_lines: list[str] = []

        todo: GreatTodo | None = None
        for line in todo_txt.read_text().split("\n"):
            for word in line.strip().split(" "):
                if word == f"id:{key}":
                    todo = GreatTodo.from_line(line).unwrap()
                    break
            else:
                new_lines.append(line)

        todo_txt.write_text("\n".join(new_lines))

        return Ok(todo)

    def update(self, key: str, todo: GreatTodo, /) -> ErisResult[GreatTodo]:
        """Overwrite an existing Todo on disk."""
        todo_txt = self.todo_group.path_map.get(key)
        if todo_txt is None:
            logger.info(
                "No todo appears to exist with the given key. Adding new todo"
                " instead...",
                key=key,
                todo=todo,
            )
            self.add(todo, key=key)
            return Ok(todo)

        all_lines = []

        old_todo: GreatTodo | None = None
        for line in todo_txt.read_text().split("\n"):
            line = line.strip()
            if not line:
                continue

            if any(w == f"id:{key}" for w in line.split(" ")):
                if todo.to_line() == line:
                    return Ok(todo)

                old_todo = GreatTodo.from_line(line).unwrap()
            else:
                all_lines.append(line)

        if old_todo is None:
            logger.warning(
                "No todo found with this key despite matching todo.txt file?"
                " Adding new todo instead...",
                key=key,
                todo=todo,
            )
            self.add(todo, key=key)
            return Ok(todo)

        all_todos = [GreatTodo.from_line(line).unwrap() for line in all_lines]
        all_todos.append(todo)
        with todo_txt.open("w") as f:
            f.write("\n".join(t.to_line() for t in sorted(all_todos)))

        return Ok(old_todo)

    def get_by_tag(self, tag: GreatTag) -> ErisResult[list[GreatTodo]]:
        """Get Todos from disk by using a tag.

        Retrieves a list of Todos from disk by using another Todo's properties
        as search criteria.
        """

        todos: list[GreatTodo] = []
        ids: set[str] = set()
        todo_group = self.todo_group
        for child_tag in tag.tags:
            for todo in todo_group.filter_by(
                contexts=child_tag.contexts,
                create_date_ranges=child_tag.create_date_ranges,
                desc_filters=child_tag.desc_filters,
                done_date_ranges=child_tag.done_date_ranges,
                done=child_tag.done,
                epics=child_tag.epics,
                metadata_filters=child_tag.metadata_filters,
                priorities=child_tag.priorities,
                projects=child_tag.projects,
            ):
                if todo.ident not in ids:
                    ids.add(todo.ident)
                    todos.append(todo)
        return Ok(todos)

    def remove_by_tag(self, tag: GreatTag) -> ErisResult[list[GreatTodo]]:
        """Remove a Todo from disk by using a tag.

        Removes a list of Todos from disk by using another Todo's properties
        as search criteria.
        """
        removed_todos = self.get_by_tag(tag).unwrap()
        for todo in removed_todos:
            self.remove(todo.ident).unwrap()
        return Ok(removed_todos)

    def all(self) -> ErisResult[list[GreatTodo]]:
        """Retreive all Todos stored on disk."""
        return Ok(list(self.todo_group))
