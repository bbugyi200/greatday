"""Contains greatday's custom Todo types."""

from __future__ import annotations

from magodo import MagicTodoMixin
from magodo.spells import group_tags

from ._spells import DAILY_SPELLS, INBOX_SPELLS


class DailyTodo(MagicTodoMixin):
    """Custom MagicTodo type used when working with Todos in the daily file."""

    spells = DAILY_SPELLS
    post_spells = [group_tags]


class InboxTodo(MagicTodoMixin):
    """Custom MagicTodo type used when adding a new Todo to inbox."""

    spells = INBOX_SPELLS
    post_spells = [group_tags]
