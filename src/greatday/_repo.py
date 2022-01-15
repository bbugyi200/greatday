"""Contains the GreatRepo class."""

from __future__ import annotations

from pathlib import Path

from clack import xdg
from eris import ErisResult, Ok
from potoroo import Repository
from typist import PathLike

from . import APP_NAME
from ._todo import GreatTodo


class GreatRepo(Repository[str, GreatTodo]):
    """Repo that stores Todos on disk."""

    def __init__(self, data_dir: PathLike = None) -> None:
        data_dir = (
            xdg.get_full_dir("data", APP_NAME)
            if data_dir is None
            else Path(data_dir)
        )
        self.root = data_dir / "todos"
        self.root.mkdir(parents=True, exist_ok=True)

    def add(self, item: GreatTodo) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """
        return Ok(item.desc)

    def get(self, key: str) -> ErisResult[GreatTodo | None]:
        """Retrieve a Todo from disk."""

    def remove(self, key: str) -> ErisResult[GreatTodo | None]:
        """Remove a Todo from disk."""

    def update(self, key: str, item: GreatTodo) -> ErisResult[GreatTodo]:
        """Overwrite an existing Todo on disk."""
