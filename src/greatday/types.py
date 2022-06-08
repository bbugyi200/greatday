"""Custom types used by greatday."""

from typing import Any, Literal, Protocol, TypeVar

from magodo.types import AbstractTodo
from sqlalchemy.future import Engine


T = TypeVar("T", bound=AbstractTodo)

YesNoDefault = Literal["n", "default", "y"]


class CreateEngineType(Protocol):
    """The type of a `db.create_engine()` callable."""

    def __call__(self, url: str, /, **kwargs: Any) -> Engine:
        """The function's call signature."""
