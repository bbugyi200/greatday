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
from ._repo import GreatRepo, Tag


logger = Logger(__name__)


class GreatSession(UnitOfWork[GreatRepo]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(
        self,
        data_dir: PathLike,
        repo_path: PathLike,
        tag: Tag,
        *,
        name: str = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self._path = Path(repo_path)

        prefix = None if name is None else f"{name}."
        _, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".txt")
        self.path = Path(temp_path)

        self._temp_repo = GreatRepo(self.data_dir, self.path)

        self._master_repo = GreatRepo(self.data_dir, self._path)
        for todo in self._master_repo.get_by_tag(tag).unwrap():
            self.repo.add(todo, key=todo.ident)

        self._old_todos = list(self._temp_repo.todo_group)

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
        old_todo_keys = [todo.ident for todo in self._old_todos]
        new_todos = {}
        for todo in self.repo.todo_group:
            key = todo.ident
            if key == NULL_ID:
                logger.info("New todo was added while editing?", todo=todo)
                key = self._master_repo.add(todo).unwrap()
                new_todos[key] = todo
            else:
                self._master_repo.update(key, todo).unwrap()
                if key in old_todo_keys:
                    old_todo_keys.remove(key)

        if new_todos:
            old_lines = self.path.read_text().split("\n")
            self.path.write_text(
                "\n".join(line for line in old_lines if " id:" in line)
            )

        for key, todo in new_todos.items():
            self.repo.add(todo, key=key)

        for key in old_todo_keys:
            removed_todo = self._master_repo.remove(key).unwrap()
            if removed_todo is not None:
                self._old_todos.remove(removed_todo)

    def rollback(self) -> None:
        """Revert any changes made while in this GreatSession's with-block."""

    @property
    def repo(self) -> GreatRepo:
        """Returns the GreatRepo object associated with this GreatSession."""
        return self._temp_repo
