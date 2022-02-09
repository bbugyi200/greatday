"""Custom types used by greatday."""

from typing import Literal, TypeVar

from magodo.types import AbstractTodo


T = TypeVar("T", bound=AbstractTodo)

YesNoPrompt = Literal["n", "prompt", "y"]
