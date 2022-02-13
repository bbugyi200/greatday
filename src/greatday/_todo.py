"""Contains greatday's custom Todo types."""

from __future__ import annotations

from magodo import MagicTodoMixin

from . import _spells as spells
from ._ids import NULL_ID


class GreatTodo(MagicTodoMixin):
    """Custom MagicTodo type used when working with Todos in the daily file."""

    pre_todo_spells = spells.GREAT_PRE_TODO_SPELLS
    todo_spells = spells.GREAT_TODO_SPELLS
    post_todo_spells = spells.GREAT_POST_TODO_SPELLS

    to_line_spells = spells.GREAT_TO_LINE_SPELLS
    from_line_spells = spells.GREAT_FROM_LINE_SPELLS

    @property
    def ident(self) -> str:
        """Returns this Todo's unique identifier."""
        result = self.metadata.get("id", NULL_ID)
        assert isinstance(result, str)
        return result
