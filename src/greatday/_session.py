"""Contains the GreatSession class."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from types import TracebackType
from typing import Type

from magodo import TodoGroup
from potoroo import UnitOfWork
from typist import PathLike

from ._repo import GreatRepo
from ._todo import GreatTodo


class GreatSession(UnitOfWork[GreatRepo]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(self, path: PathLike) -> None:
        path = Path(path)
        self._path = path

        _, temp_path = tempfile.mkstemp(suffix=path.stem)
        self.path = Path(temp_path)

        self._repo = GreatRepo(path)

    def __enter__(self) -> GreatSession:
        """Called before entering a GreatSession with-block."""
        self.repo.todo_group.to_disk(self.path)
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
        todo_group = TodoGroup.from_path(GreatTodo, self.path)
        for todo in todo_group:
            key = todo.metadata["id"]
            self.repo.update(key, todo)

    def rollback(self) -> None:
        """Revert any changes made while in this GreatSession's with-block."""

    @property
    def repo(self) -> GreatRepo:
        """Returns the GreatRepo object associated with this GreatSession."""
        return self._repo
