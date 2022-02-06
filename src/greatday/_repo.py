"""Contains the Repo class."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from pathlib import Path
from typing import Iterable, Type

from eris import ErisResult, Ok
from magodo import TodoGroup
from potoroo import TaggedRepo
from typist import PathLike

from ._ids import init_next_todo_id
from ._todo import GreatTodo


@dataclass(frozen=True)
class Tag:
    """Tag used to filter Todos."""

    contexts: Iterable[str]


class GreatRepo(TaggedRepo[str, GreatTodo, Tag]):
    """Repo that stores Todos on disk."""

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)

        self._todo_group: TodoGroup | None = None
        self._reload_todo_group = False

    def add(self, todo: GreatTodo, /, *, key: str = None) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        if key is None:
            key = init_next_todo_id(self.path)

        line = todo.to_line()
        line = line + f" id:{key}"
        todo = GreatTodo.from_line(line).unwrap()

        todos: list[GreatTodo] = [todo]

        if self.path.is_dir() or (
            not self.path.exists() and self.path.suffix != ".txt"
        ):
            txt_path = init_yyyymm_path(self.path, date=todo.create_date)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            txt_path = self.path

        if txt_path.exists():
            todo_group = TodoGroup.from_path(GreatTodo, txt_path)
            todos.extend(todo_group)

        with txt_path.open("w") as f:
            f.write(
                "\n".join(GreatTodo.to_line() for GreatTodo in sorted(todos))
            )

        return Ok(key)

    @property
    def todo_group(self) -> TodoGroup[GreatTodo]:
        """Returns the TodoGroup associated with this GreatRepo."""
        if self._todo_group is None or self._reload_todo_group:
            self._todo_group = TodoGroup.from_path(GreatTodo, self.path)
        return self._todo_group

    def get(self, key: str) -> ErisResult[GreatTodo | None]:
        """Retrieve a Todo from disk."""

    def remove(self, key: str) -> ErisResult[GreatTodo | None]:
        """Remove a Todo from disk."""

    def update(self, key: str, todo: GreatTodo, /) -> ErisResult[GreatTodo]:
        """Overwrite an existing Todo on disk."""

    def get_by_tag(self, tag: Tag) -> ErisResult[list[GreatTodo]]:
        """Get Todos from disk by using a tag.

        Retrieves a list of Todos from disk by using another Todo's properties
        as search criteria.
        """

        return Ok(list(self.todo_group.filter_by(contexts=tag.contexts)))

    def remove_by_tag(self, tag: Tag) -> ErisResult[list[GreatTodo]]:
        """Remove a Todo from disk by using a tag.

        Removes a list of Todos from disk by using another Todo's properties
        as search criteria.
        """


def init_yyyymm_path(root: PathLike, *, date: dt.date = None) -> Path:
    """Returns a Path of the form /path/to/root/YYYY/MM.txt.

    NOTE: Creates the /path/to/root/YYYY directory if necessary.
    """
    root = Path(root)
    if date is None:
        date = dt.date.today()

    year = date.year
    month = date.month

    result = root / str(year) / f"{month:0>2}.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    return result
