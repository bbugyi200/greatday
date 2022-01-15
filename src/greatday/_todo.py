"""Contains the GreatTodo class."""

from __future__ import annotations

from magodo import MagicTodoMixin

from ._spells import GREAT_SPELLS


class GreatTodo(MagicTodoMixin):
    """Custom MagicTodo type used by greatday."""

    spells = GREAT_SPELLS
