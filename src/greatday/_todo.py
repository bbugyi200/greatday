"""Contains greatday's custom Todo types."""

from __future__ import annotations

from magodo import MagicTodoMixin

from . import _spells as spells


class GreatTodo(MagicTodoMixin):
    """Custom MagicTodo type used when working with Todos in the daily file."""

    todo_spells = spells.GREAT_TODO_SPELLS
    to_line_spells = spells.GREAT_TO_LINE_SPELLS
    from_line_spells = spells.GREAT_FROM_LINE_SPELLS
