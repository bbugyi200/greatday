"""Contains greatday's custom Todo types."""

from __future__ import annotations

from typing import List

from magodo import MagicTodoMixin
from magodo.types import TodoSpell

from ._spells import INBOX_SPELLS


class InboxTodo(MagicTodoMixin):
    """Custom MagicTodo type used when adding a new Todo to inbox."""

    pre_spells: List[TodoSpell] = []
    spells = INBOX_SPELLS
