"""Contains greatday's custom Todo types."""

from __future__ import annotations

from magodo import MagicTodoMixin
from magodo.spells import group_tags

from ._spells import TO_DAILY_SPELLS, TO_INBOX_SPELLS


class ToDailyTodo(MagicTodoMixin):
    """Custom MagicTodo type used when working with Todos in the daily file."""

    todo_spells = TO_DAILY_SPELLS + [group_tags]


class ToInboxTodo(MagicTodoMixin):
    """Custom MagicTodo type used when adding a new Todo to inbox."""

    todo_spells = TO_INBOX_SPELLS + [group_tags]
