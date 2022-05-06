"""Contains the GreatSession class."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from types import TracebackType
from typing import Type

from logrus import Logger
from potoroo import UnitOfWork
from typist import PathLike

from ._ids import NULL_ID
from ._repo import GreatRepo
from ._tag import Tag


logger = Logger(__name__)


class GreatSession(UnitOfWork[GreatRepo]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(
        self,
        data_dir: PathLike,
        tag: Tag = None,
        *,
        name: str = None,
    ) -> None:
        self.data_dir = Path(data_dir)

        prefix = None if name is None else f"{name}."
        _, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".txt")
        self.path = Path(temp_path)

        self._temp_repo = GreatRepo(self.data_dir, self.path)

        self._master_repo = GreatRepo(self.data_dir)
        if tag is not None:
            for todo in self._master_repo.get_by_tag(tag).unwrap():
                self.repo.add(todo, key=todo.ident)

        self._old_todo_map = {
            todo.ident: todo for todo in self._temp_repo.todo_group
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
                self._master_repo.update(key, todo).unwrap()

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
        return self._temp_repo
