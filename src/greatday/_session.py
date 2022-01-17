"""Contains the GreatSession class."""

from __future__ import annotations

from types import TracebackType
from typing import Type

from potoroo import UnitOfWork

from ._repo import GreatRepo


class GreatSession(UnitOfWork[GreatRepo]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(self) -> None:
        pass

    def __enter__(self) -> GreatSession:
        pass

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
