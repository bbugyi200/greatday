"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

import datetime as dt
from typing import List

import magodo
from magodo.spells import (
    DEFAULT_FROM_LINE_SPELLS,
    DEFAULT_TO_LINE_SPELLS,
    DEFAULT_TODO_SPELLS,
    register_line_spell_factory,
    register_todo_spell_factory,
)
from magodo.types import LineSpell, T, TodoSpell

from ._common import CTX_TODAY, drop_word_from_desc


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

    if CTX_TODAY not in todo.contexts:
        return todo

    today = dt.date.today()
    if todo.done_date == today:
        return todo

    contexts = [ctx for ctx in todo.contexts if ctx != CTX_TODAY]
    desc = drop_word_from_desc(todo.desc, f"@{CTX_TODAY}")
    return todo.new(desc=desc, contexts=contexts)


@todo_spell
def recur_spell(todo: T) -> T:
    """Handles the 'recur:' metatag."""
    mdata = todo.metadata

    def get_tdelta(spec: str) -> dt.timedelta:
        """Converts a string spec to a timedelta."""
        assert spec[-1] == "d"
        days = int(spec[:-1])
        return dt.timedelta(days=days)

    if not todo.done:
        return todo

    recur = mdata.get("recur")
    if not recur:
        return todo

    tickle = mdata.get("tickle")
    if not tickle:
        return todo

    assert isinstance(recur, str)
    tdelta = get_tdelta(recur)

    metadata = dict(mdata.items())
    today = dt.date.today()
    next_tickle_date = today + tdelta
    next_tickle_str = magodo.from_date(next_tickle_date)
    metadata["tickle"] = next_tickle_str

    if "dtime" in metadata:
        del metadata["dtime"]

    desc_words = todo.desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if word.startswith("tickle:"):
            new_desc_words.append(f"tickle:{next_tickle_str}")
        elif word.startswith("dtime:"):
            continue
        else:
            new_desc_words.append(word)

    desc = " ".join(new_desc_words)

    return todo.new(desc=desc, metadata=metadata, done=False, done_date=None)


@todo_spell
def appt_todos(todo: T) -> T:
    """Adds priority of (T) to todos with an appt:HHMM tag."""
    if not todo.metadata.get("appt"):
        return todo

    if todo.priority != magodo.DEFAULT_PRIORITY:
        return todo

    if todo.done or todo.done_date:
        return todo

    return todo.new(priority="T")
