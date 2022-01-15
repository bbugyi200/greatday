"""Contains the GreatRepo class."""

from __future__ import annotations

from clack import xdg
from eris import ErisResult
from potoroo import Repository

from . import APP_NAME
from ._config import Config
from ._todo import GreatTodo


class GreatRepo(Repository[str, GreatTodo]):
    """Repo that stores Todos on disk."""

    def __init__(self, cfg: Config) -> None:
        data_dir = (
            xdg.get_full_dir("data", APP_NAME)
            if cfg.data_dir is None
            else cfg.data_dir
        )
        self.root = data_dir / "todos"
        self.root.mkdir(parents=True, exist_ok=True)

    def add(self, item: GreatTodo) -> ErisResult[str]:
        """Write a new Todo to disk.

        Returns a unique identifier that has been associated with this Todo.
        """

    def get(self, key: str) -> ErisResult[GreatTodo | None]:
        """Retrieve a Todo from disk."""

    def remove(self, key: str) -> ErisResult[GreatTodo | None]:
        """Remove a Todo from disk."""

    def update(self, key: str, item: GreatTodo) -> ErisResult[GreatTodo]:
        """Overwrite an existing Todo on disk."""
