"""Contains the GreatRepo class."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Container

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

        self.data_root = data_dir

        self.todos_root = self.data_root / "todos"

        self.todos_open = self.todos_root / "open"
        self.todos_open.mkdir(parents=True, exist_ok=True)

    def add(self, item: Todo_T) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        next_id = fetch_next_todo_id(self.data_root)
        line = item.to_line()
        line = line + f" id:{next_id}"
        item = type(item).from_line(line).unwrap()

        todos: list[Todo_T] = [item]
        yyymm_path = init_yyyymm_path(self.todos_open)
        if yyymm_path.exists():
            todo_group = TodoGroup.from_path(type(item), yyymm_path)
            todos.extend(todo_group)

        with yyymm_path.open("w") as f:
            f.write("\n".join(T.to_line() for T in sorted(todos)))

        return Ok(next_id)

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


def fetch_next_todo_id(root: PathLike) -> str:
    """Retrieves the next valid todo ID."""
    root = Path(root)
    last_id_path = root / "last_todo_id"

    def ID(next_id: str) -> str:
        with last_id_path.open("w+"):
            last_id_path.write_text(next_id)
        return next_id

    if last_id_path.exists():
        last_id = last_id_path.read_text().strip()
        next_id = next_todo_id(last_id)
        return ID(next_id)
    else:
        return ID("0")


def next_todo_id(last_id: str) -> str:
    """Determines the next ID from the last ID.

    Examples:
        >>> next_todo_id('0')
        '1'

        >>> next_todo_id('9')
        'A'

        >>> next_todo_id('Z')
        '00'

        >>> next_todo_id('ZZ')
        '000'

        >>> next_todo_id('AZ')
        'B0'

        >>> next_todo_id('BM9')
        'BMA'

        >>> next_todo_id('BMZ')
        'BN0'

        >>> next_todo_id('BZZ')
        'C00'

        # we skip 'I', since it can be confused with '1'...
        >>> next_todo_id('BZH')
        'BZJ'

        # we skip 'O', since it can be confused with '0'...
        >>> next_todo_id('BZN')
        'BZP'
    """
    last_char = last_id[-1]
    if last_char == "9":
        return last_id[:-1] + "A"
    elif last_char == "Z":
        for i, ch in enumerate(reversed(last_id)):
            if ch != "Z":
                idx = len(last_id) - (i + 1)
                zeros = "0" * i
                return last_id[:idx] + next_char(last_id[idx]) + zeros

        zeros = "0" * len(last_id)
        return "0" + zeros
    else:
        return last_id[:-1] + next_char(last_char)


def next_char(ch: str, *, blacklist: Container[str] = ("I", "O")) -> str:
    """Returns the next allowable character (to be used as apart of ID)."""
    result = chr(ord(ch) + 1)
    while result in blacklist:
        result = chr(ord(result) + 1)
    return result
