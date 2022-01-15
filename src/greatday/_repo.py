"""Contains the GreatRepo class."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from clack import xdg
from eris import ErisResult, Ok
from magodo import TodoGroup
from magodo.types import Todo_T
from potoroo import Repository
from typist import PathLike

from . import APP_NAME


class GreatRepo(Repository[str, Todo_T]):
    """Repo that stores Todos on disk."""

    def __init__(self, data_dir: PathLike = None) -> None:
        data_dir = (
            xdg.get_full_dir("data", APP_NAME)
            if data_dir is None
            else Path(data_dir)
        )

        self.data_root = data_dir / "todos"

        self.data_open = self.data_root / "open"
        self.data_open.mkdir(parents=True, exist_ok=True)

    def add(self, item: Todo_T) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        todos: list[Todo_T] = [item]
        yyymm_path = init_yyyymm_path(self.data_open)
        if yyymm_path.exists():
            todo_group = TodoGroup.from_path(type(item), yyymm_path)
            todos.extend(todo_group)

        with yyymm_path.open("w") as f:
            f.write("\n".join(T.to_line() for T in sorted(todos)))

        return Ok(item.to_line())

    def get(self, key: str) -> ErisResult[Todo_T | None]:
        """Retrieve a Todo from disk."""

    def remove(self, key: str) -> ErisResult[Todo_T | None]:
        """Remove a Todo from disk."""

    def update(self, key: str, item: Todo_T) -> ErisResult[Todo_T]:
        """Overwrite an existing Todo on disk."""


def init_yyyymm_path(base: PathLike) -> Path:
    """Returns a Path of the form /path/to/base/YYYY/MM.txt.

    NOTE: Creates the /path/to/base/YYYY directory if necessary.
    """
    base = Path(base)

    today = dt.date.today()
    year = today.year
    month = today.month

    result = base / str(year) / f"{month:0>2}.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    return result
