"""Contains the GreatSession class."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
from types import TracebackType
from typing import Type

from potoroo import UnitOfWork
from typist import PathLike

from ._repo import GreatRepo
from .types import T


class GreatSession(UnitOfWork[GreatRepo[T]]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(self, path: PathLike, todo_type: Type[T]) -> None:
        path = Path(path)
        self.path = path

        _, backup = tempfile.mkstemp(suffix=path.stem)
        self.backup = Path(backup)

        self._repo: GreatRepo[T] = GreatRepo(backup, todo_type)

    def __enter__(self) -> GreatSession:
        """Called before entering a GreatSession with-block."""
        shutil.copyfile(self.path, self.backup)
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

        os.unlink(self.backup)

    def commit(self) -> None:
        """Commit our changes.

        We achieve this by copying the contents of the backup file created on
        instantiation back to the original.
        """
        shutil.copyfile(self.backup, self.path)

    def rollback(self) -> None:
        """Revert any changes made while in this GreatSession's with-block."""
        shutil.copyfile(self.path, self.backup)
        self._repo = GreatRepo(self.repo.path, self.repo.todo_type)

    @property
    def repo(self) -> GreatRepo[T]:
        """Returns the GreatRepo object associated with this GreatSession."""
        return self._repo
