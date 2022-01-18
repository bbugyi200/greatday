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

    def __init__(self, data_dir: PathLike, path: PathLike) -> None:
        path = Path(path)
        self._path = path

        _, backup = tempfile.mkstemp(suffix=path.stem)
        self._backup = Path(backup)

        self._repo: GreatRepo[T] = GreatRepo(data_dir, backup)

    def __enter__(self) -> GreatSession:
        """Called before entering a GreatSession with-block."""
        shutil.copyfile(self._path, self._backup)
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

        os.unlink(self._backup)

    def commit(self) -> None:
        """Commit our changes.

        We achieve this by copying the contents of the backup file created on
        instantiation back to the original.
        """
        shutil.copyfile(self._backup, self._path)

    def rollback(self) -> None:
        """Revert any changes made while in this GreatSession's with-block."""
        shutil.copyfile(self._path, self._backup)
        self._repo = GreatRepo(self.repo.data_dir, self._backup)

    @property
    def repo(self) -> GreatRepo[T]:
        """Returns the GreatRepo object associated with this GreatSession."""
        return self._repo
