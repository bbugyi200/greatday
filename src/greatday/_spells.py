"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

import datetime as dt
from typing import List

import magodo
from magodo.spells import (
    DEFAULT_FROM_LINE_SPELLS,
    DEFAULT_POST_TODO_SPELLS,
    DEFAULT_PRE_TODO_SPELLS,
    DEFAULT_TO_LINE_SPELLS,
    DEFAULT_TODO_SPELLS,
    register_line_spell_factory,
    register_todo_spell_factory,
)
from magodo.types import LineSpell, T, TodoSpell

from ._common import CTX_TODAY, drop_word_from_desc, get_relative_date


GREAT_PRE_TODO_SPELLS: List[TodoSpell] = list(DEFAULT_PRE_TODO_SPELLS)
pre_todo_spell = register_todo_spell_factory(GREAT_PRE_TODO_SPELLS)

GREAT_TODO_SPELLS: List[TodoSpell] = list(DEFAULT_TODO_SPELLS)
todo_spell = register_todo_spell_factory(GREAT_TODO_SPELLS)

GREAT_POST_TODO_SPELLS: List[TodoSpell] = list(DEFAULT_POST_TODO_SPELLS)
post_todo_spell = register_todo_spell_factory(GREAT_POST_TODO_SPELLS)

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

    if not todo.done:
        return todo

    recur = mdata.get("recur")
    if not recur:
        return todo

    tickle = mdata.get("tickle")
    assert isinstance(tickle, str)
    if not tickle:
        return todo

    assert isinstance(recur, str)
    next_date = get_relative_date(recur)

    metadata = dict(mdata.items())

    today = dt.date.today()
    if magodo.to_date(tickle) <= today:
        next_tickle_date = next_date
        new_tickle = magodo.from_date(next_tickle_date)
        metadata["tickle"] = new_tickle
    else:
        new_tickle = tickle

    if "dtime" in metadata:
        del metadata["dtime"]

    desc_words = todo.desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if word.startswith("tickle:"):
            new_desc_words.append(f"tickle:{new_tickle}")
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


@todo_spell
def x_points(todo: T) -> T:
    """Handles metatags of the form 'x:N' at the start of a todo line."""
    x = todo.metadata.get("x")
    if not x or len(x) >= 4:
        return todo

    if not todo.desc.startswith("x:"):
        return todo

    metadata = dict(todo.metadata.items())
    points = metadata["x"]
    del metadata["x"]
    metadata["points"] = points

    desc = " ".join(todo.desc.split(" ")[1:]) + f" points:{points}"

    new_todo = todo.new(desc=desc, done=True, metadata=metadata)
    line = new_todo.to_line()
    return type(todo).from_line(line).unwrap()


@todo_spell
def points_metatag(todo: T) -> T:
    """Handles the 'points:N' metatag."""
    desc = todo.desc
    points = todo.metadata.get("points")
    metadata = todo.metadata

    P = todo.metadata.get("p")
    if P:
        points = P

        metadata = dict(metadata.items())
        metadata["points"] = points

        del metadata["p"]
        desc = drop_word_from_desc(desc, f"p:{points}")

        desc = desc + f" points:{points}"

    if not points:
        return todo

    priority = todo.priority
    if not todo.done and priority > "I":
        priority = "I"

    return todo.new(desc=desc, metadata=metadata, priority=priority)
