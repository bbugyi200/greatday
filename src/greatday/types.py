"""Custom types used by greatday."""

from typing import TypeVar

from magodo.types import AbstractTodo


T = TypeVar("T", bound=AbstractTodo)
U = TypeVar("U", bound=AbstractTodo)
