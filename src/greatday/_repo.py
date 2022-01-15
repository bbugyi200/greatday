"""Contains the Repo class."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Container

from eris import ErisResult, Ok
from magodo import Todo, TodoGroup
from magodo.types import Todo_T
from potoroo import TaggedRepo
from typist import PathLike


class GreatDayRepo(TaggedRepo[str, Todo_T, Todo]):
    """Repo that stores Todos on disk."""

    def __init__(self, data_dir: PathLike, path: PathLike) -> None:
        self.data_dir = Path(data_dir)
        self.path = Path(path)

    def add(self, todo: Todo_T, /, *, key: str = None) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        if key is None:
            key = init_next_todo_id(self.data_dir)

        line = todo.to_line()
        line = line + f" id:{key}"
        todo = type(todo).from_line(line).unwrap()

        todos: list[Todo_T] = [todo]
        if self.path.is_dir() or (
            not self.path.exists() and self.path.suffix != ".txt"
        ):
            txt_path = init_yyyymm_path(self.path, date=todo.create_date)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            txt_path = self.path

        if txt_path.exists():
            todo_group = TodoGroup.from_path(type(todo), txt_path)
            todos.extend(todo_group)

        with txt_path.open("w") as f:
            f.write("\n".join(T.to_line() for T in sorted(todos)))

        return Ok(key)

    def get(self, key: str) -> ErisResult[Todo_T | None]:
        """Retrieve a Todo from disk."""

    def remove(self, key: str) -> ErisResult[Todo_T | None]:
        """Remove a Todo from disk."""

    def update(self, key: str, todo: Todo_T, /) -> ErisResult[Todo_T]:
        """Overwrite an existing Todo on disk."""

    def get_by_tag(self, tag: Todo) -> ErisResult[list[Todo_T]]:
        """Get Todos from disk by using a tag.

        Retrieves a list of Todos from disk by using another Todo's properties
        as search criteria.
        """

    def remove_by_tag(self, tag: Todo) -> ErisResult[list[Todo_T]]:
        """Remove a Todo from disk by using a tag.

        Removes a list of Todos from disk by using another Todo's properties
        as search criteria.
        """


def init_yyyymm_path(base: PathLike, *, date: dt.date = None) -> Path:
    """Returns a Path of the form /path/to/base/YYYY/MM.txt.

    NOTE: Creates the /path/to/base/YYYY directory if necessary.
    """
    if date is None:
        date = dt.date.today()

    base = Path(base)

    year = date.year
    month = date.month

    result = base / str(year) / f"{month:0>2}.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    return result


def init_next_todo_id(root: PathLike) -> str:
    """Retrieves the next valid todo ID.

    Side Effects:
        * Attempts to read last ID from disk.
        * Writes the returned ID to disk.
    """
    root = Path(root)
    last_id_path = root / "last_todo_id"

    def ID(next_id: str) -> str:
        last_id_path.parent.mkdir(parents=True, exist_ok=True)
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
