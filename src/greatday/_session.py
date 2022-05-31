"""Contains the GreatSession class."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import tempfile
from types import TracebackType
from typing import Type

from logrus import Logger
import magodo
from potoroo import UnitOfWork
from typist import PathLike

from ._dates import get_relative_date
from ._ids import NULL_ID
from ._repo import GreatRepo
from ._tag import GreatTag
from ._todo import GreatTodo


logger = Logger(__name__)


class GreatSession(UnitOfWork[GreatRepo]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(
        self,
        data_dir: PathLike,
        tag: GreatTag = None,
        *,
        name: str = None,
    ) -> None:
        self.data_dir = Path(data_dir)

        prefix = None if name is None else f"{name}."
        _, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".txt")
        self.path = Path(temp_path)

        self._repo = GreatRepo(self.data_dir, self.path)

        self._master_repo = GreatRepo(self.data_dir)
        if tag is not None:
            for todo in self._master_repo.get_by_tag(tag).unwrap():
                self._repo.add(todo, key=todo.ident)

        self._old_todo_map = {
            todo.ident: todo for todo in self._repo.todo_group
        }

    def __enter__(self) -> GreatSession:
        """Called before entering a GreatSession with-block."""
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Called before exiting a GreatSession with-block."""
        del exc_type
        del exc_value
        del traceback

        os.unlink(self.path)

    def commit(self) -> None:
        """Commit our changes.

        We achieve this by copying the contents of the backup file created on
        instantiation back to the original.
        """
        removed_todo_keys = list(self._old_todo_map.keys())
        new_todos = {}
        for todo in self.repo.todo_group:
            key = todo.ident
            if key in removed_todo_keys:
                removed_todo_keys.remove(key)

            old_todo = self._old_todo_map.get(key)
            if key == NULL_ID:
                logger.info("New todo was added while editing?", todo=todo)
                key = self._master_repo.add(todo).unwrap()
                new_todos[key] = todo
            elif todo != old_todo:
                _commit_todo_changes(self._master_repo, todo, old_todo)

        if new_todos:
            old_lines = self.path.read_text().split("\n")
            self.path.write_text(
                "\n".join(line for line in old_lines if " id:" in line)
            )

        for key, todo in new_todos.items():
            self.repo.add(todo, key=key)

        for key in removed_todo_keys:
            removed_todo = self._master_repo.remove(key).unwrap()
            if removed_todo is not None:
                del self._old_todo_map[removed_todo.ident]

    def rollback(self) -> None:
        """Revert any changes made while in this GreatSession's with-block."""

    @property
    def repo(self) -> GreatRepo:
        """Returns the GreatRepo object associated with this GreatSession."""
        return self._repo


def _commit_todo_changes(
    repo: GreatRepo, todo: GreatTodo, old_todo: GreatTodo | None
) -> None:
    """Updates todo in repo.

    This function also handles recurring todos (i.e. todos with the
    'recur' metatag).
    """
    recur = todo.metadata.get("recur")
    until = todo.metadata.get("until")
    expired = bool(
        todo.done_date and until and magodo.to_date(until) <= todo.done_date
    )
    if (
        old_todo
        and todo.done_date
        and not old_todo.done_date
        and recur
        and not expired
        and not todo.metadata.get("tickle")
    ):
        next_metadata = dict(todo.metadata.items())

        # set 'prev' and 'xp' metatags for next todo...
        next_metadata["prev"] = next_metadata["id"]
        del next_metadata["id"]
        if next_metadata.get("p"):
            del next_metadata["p"]

        # set 'due' metatag for next todo...
        due = todo.metadata.get("due")
        if recur.islower() or due is None:
            start_date = todo.done_date
        else:
            start_date = magodo.to_date(due)

        next_date = get_relative_date(recur, start_date=start_date)
        next_metadata["due"] = magodo.from_date(next_date)

        # set creation date + clear creation/done time for next todo...
        next_create_date = dt.date.today()
        for key in ["ctime", "dtime"]:
            if key in next_metadata:
                del next_metadata[key]

        # add next todo to repo...
        next_todo = todo.new(
            create_date=next_create_date,
            done=False,
            done_date=None,
            metadata=next_metadata,
            priority=old_todo.priority,
        )
        next_key = repo.add(next_todo).unwrap()

        # add 'next' metatag to old todo...
        metadata = dict(todo.metadata.items())
        metadata["next"] = next_key
        todo = todo.new(metadata=metadata)

    repo.update(todo.ident, todo).unwrap()
