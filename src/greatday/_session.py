"""Contains the GreatSession class."""

from __future__ import annotations

from types import TracebackType
from typing import Type

from potoroo import UnitOfWork
from typist import PathLike

from ._repo import GreatRepo
from .types import T


class GreatSession(UnitOfWork[GreatRepo[T]]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(self, data_dir: PathLike, path: PathLike) -> None:
        self._path = path
        self._repo: GreatRepo[T] = GreatRepo(data_dir, path)

    def __enter__(self) -> GreatSession:
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type
        del exc_value
        del traceback

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    @property
    def repo(self) -> GreatRepo[T]:
        return self._repo
