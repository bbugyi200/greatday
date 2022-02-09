"""Contains the Repo class."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from pathlib import Path
from typing import Iterable, Mapping

from eris import ErisResult, Ok
from logrus import Logger
from magodo import TodoGroup
from magodo.types import MetadataChecker, Priority
from potoroo import TaggedRepo
from typist import PathLike

from ._ids import NULL_ID, init_next_todo_id
from ._todo import GreatTodo


logger = Logger(__name__)


@dataclass(frozen=True)
class Tag:
    """Tag used to filter Todos."""

    contexts: Iterable[str] = ()
    done: bool | None = None
    metadata_checks: Mapping[str, MetadataChecker] | None = None
    priorities: Iterable[Priority] = ()
    projects: Iterable[str] = ()


class GreatRepo(TaggedRepo[str, GreatTodo, Tag]):
    """Repo that stores Todos on disk."""

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)

        self._todo_group: TodoGroup | None = None

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
            key = init_next_todo_id(self.path)
        else:
            drop_old_key = True

        mdata = dict(todo.metadata.items())

        old_key = mdata.get("id")
        if (drop_old_key and old_key != key) or not old_key:
            metadata = dict(mdata.items())
            metadata.update({"id": key})
            todo = todo.new(metadata=metadata)

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

        if todo is None:
            return Ok(None)
        else:
            return Ok(todo)

    def update(self, key: str, todo: GreatTodo, /) -> ErisResult[GreatTodo]:
        """Overwrite an existing Todo on disk."""
        self.remove(key).unwrap()
        self.add(todo, key=key)
        return Ok(todo)

    def get_by_tag(self, tag: Tag) -> ErisResult[list[GreatTodo]]:
        """Get Todos from disk by using a tag.

        Retrieves a list of Todos from disk by using another Todo's properties
        as search criteria.
        """

        return Ok(
            list(
                self.todo_group.filter_by(
                    contexts=tag.contexts,
                    done=tag.done,
                    metadata_checks=tag.metadata_checks,
                    priorities=tag.priorities,
                    projects=tag.projects,
                )
            )
        )

    def remove_by_tag(self, tag: Tag) -> ErisResult[list[GreatTodo]]:
        """Remove a Todo from disk by using a tag.

        Removes a list of Todos from disk by using another Todo's properties
        as search criteria.
        """
        todos = self.get_by_tag(tag).unwrap()
        for todo in todos:
            key = todo.metadata["id"]
            assert isinstance(key, str)
            self.remove(key)
        return Ok(todos)


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
