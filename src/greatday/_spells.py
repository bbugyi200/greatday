"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

import datetime as dt
from typing import List

from magodo.spells import (
    DEFAULT_FROM_LINE_SPELLS,
    DEFAULT_TO_LINE_SPELLS,
    DEFAULT_TODO_SPELLS,
    register_line_spell_factory,
    register_todo_spell_factory,
)
from magodo.types import LineSpell, T, TodoSpell


GREAT_TODO_SPELLS: List[TodoSpell] = list(DEFAULT_TODO_SPELLS)
todo_spell = register_todo_spell_factory(GREAT_TODO_SPELLS)

GREAT_TO_LINE_SPELLS: List[LineSpell] = list(DEFAULT_TO_LINE_SPELLS)
to_line_spell = register_line_spell_factory(GREAT_TO_LINE_SPELLS)

GREAT_FROM_LINE_SPELLS: List[LineSpell] = list(DEFAULT_FROM_LINE_SPELLS)
from_line_spell = register_line_spell_factory(GREAT_FROM_LINE_SPELLS)


@todo_spell
def remove_today_context(todo: T) -> T:
    """Removes the @today context from done todos completed before today."""
    if not todo.done_date:
        return todo

    if "today" not in todo.contexts:
        return todo

    today = dt.date.today()
    if todo.done_date == today:
        return todo

    contexts = [ctx for ctx in todo.contexts if ctx != "today"]
    return todo.new(contexts=contexts)
