"""Contains the Repo class."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import TypeVar

from eris import ErisResult, Ok
from magodo import Todo, TodoGroup
from magodo.types import AbstractTodo
from potoroo import TaggedRepo
from typist import PathLike

from ._ids import init_next_todo_id


T = TypeVar("T", bound=AbstractTodo)


class GreatRepo(TaggedRepo[str, T, Todo]):
    """Repo that stores Todos on disk."""

    def __init__(self, data_dir: PathLike, *paths: PathLike) -> None:
        self.data_dir = Path(data_dir)
        self.paths = [Path(p) for p in paths]

    def add(self, todo: T, /, *, key: str = None) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        if key is None:
            key = init_next_todo_id(self.data_dir)

        line = todo.to_line()
        line = line + f" id:{key}"
        todo = type(todo).from_line(line).unwrap()

        todos: list[T] = [todo]
        for path in self.paths:
            if path.is_dir() or (not path.exists() and path.suffix != ".txt"):
                txt_path = init_yyyymm_path(path, date=todo.create_date)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                txt_path = path

            if txt_path.exists():
                todo_group = TodoGroup.from_path(type(todo), txt_path)
                todos.extend(todo_group)

        with txt_path.open("w") as f:
            f.write("\n".join(T.to_line() for T in sorted(todos)))

        return Ok(key)

    def get(self, key: str) -> ErisResult[T | None]:
        """Retrieve a Todo from disk."""

    def remove(self, key: str) -> ErisResult[T | None]:
        """Remove a Todo from disk."""

    def update(self, key: str, todo: T, /) -> ErisResult[T]:
        """Overwrite an existing Todo on disk."""

    def get_by_tag(self, tag: Todo) -> ErisResult[list[T]]:
        """Get Todos from disk by using a tag.

        Retrieves a list of Todos from disk by using another Todo's properties
        as search criteria.
        """

    def remove_by_tag(self, tag: Todo) -> ErisResult[list[T]]:
        """Remove a Todo from disk by using a tag.

        Removes a list of Todos from disk by using another Todo's properties
        as search criteria.
        """


def init_yyyymm_path(base: PathLike, *, date: dt.date = None) -> Path:
    """Returns a Path of the form /path/to/base/YYYY/MM.txt.

    NOTE: Creates the /path/to/base/YYYY directory if necessary.
    """
    base = Path(base)
    if date is None:
        date = dt.date.today()

    year = date.year
    month = date.month

    result = base / str(year) / f"{month:0>2}.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    return result
