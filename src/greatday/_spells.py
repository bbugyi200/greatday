"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

import datetime as dt
from functools import partial
from typing import List

from logrus import Logger
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

from ._common import drop_word_from_desc
from ._dates import (
    RELATIVE_DATE_METATAGS,
    dt_from_date_and_hhmm,
    get_relative_date,
    matches_date_fmt,
    matches_relative_date_fmt,
)


logger = Logger(__name__)

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


def _startswith_op(x: str, y: str) -> bool:
    """Used as the value for the 'op' kwarg of `drop_word_from_desc()`."""
    return x.startswith(y)


drop_word_if_startswith = partial(drop_word_from_desc, op=_startswith_op)


###############################################################################
# First, all PRE todo spells are cast...
###############################################################################
@pre_todo_spell
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
    metadata["p"] = points

    desc = todo.desc
    desc = drop_word_if_startswith(desc, "p:")
    desc = " ".join(desc.split(" ")[1:]) + f" p:{points}"

    new_todo = todo.new(desc=desc, done=True, metadata=metadata)
    line = new_todo.to_line()
    return type(todo).from_line(line).unwrap()


###############################################################################
# Then all NORMAL todo spells are cast...
###############################################################################
@todo_spell
def snooze_spell(todo: T) -> T:
    """Handles the 'snooze' metadata tag."""
    metadata = dict(todo.metadata.items())
    s = metadata.get("s")
    if s is not None:
        metadata["snooze"] = s
        del metadata["s"]

    snooze = metadata.get("snooze")
    if snooze is None:
        return todo

    del metadata["snooze"]
    metadata["due"] = snooze

    return todo.new(metadata=metadata, priority=magodo.DEFAULT_PRIORITY)


@todo_spell
def render_relative_dates(todo: T) -> T:
    """Renders metatags that support relative dates.

    (e.g. 'due:1d' -> 'due:2022-02-16')
    """
    found_tag = False
    desc = todo.desc
    metadata = dict(todo.metadata.items())

    for key in RELATIVE_DATE_METATAGS:
        value = todo.metadata.get(key)
        if not value:
            continue

        if not matches_relative_date_fmt(value):
            continue

        found_tag = True

        new_t_or_s_date = get_relative_date(value)
        new_t_or_s = magodo.from_date(new_t_or_s_date)
        metadata[key] = new_t_or_s

        desc = drop_word_if_startswith(desc, key + ":")

    if not found_tag:
        return todo

    return todo.new(desc=desc, metadata=metadata)


@todo_spell
def due_context_spell(todo: T) -> T:
    """Converts @due context into 'due' metatag."""
    if "due" not in todo.contexts:
        return todo

    today = dt.date.today()

    contexts = [ctx for ctx in todo.contexts if ctx != "due"]
    desc = drop_word_from_desc(todo.desc, "@due")
    metadata = dict(todo.metadata.items())
    metadata["due"] = magodo.from_date(today)
    return todo.new(desc=desc, contexts=contexts, metadata=metadata)


@todo_spell
def appt_todos(todo: T) -> T:
    """Adds priority of (C) or (T) to todos with an appt:HHMM tag."""
    appt = todo.metadata.get("appt")
    if not appt:
        return todo

    if todo.done or todo.done_date:
        return todo

    due = todo.metadata.get("due")
    if due is None:
        return todo

    if not matches_date_fmt(due):
        return todo

    today = dt.date.today()
    if magodo.to_date(due) > today:
        return todo

    now = dt.datetime.now()
    appt_dt = dt_from_date_and_hhmm(today, appt)
    if appt_dt < now + dt.timedelta(minutes=30):
        priority = "C"
    else:
        priority = "T"

    return todo.new(priority=priority)


@todo_spell
def i_priority_spell(todo: T) -> T:
    """Handles todos with the in-prigress [i.e. (I)] priority."""
    start = todo.metadata.get("start")
    if todo.priority != "I":
        if start:
            metadata = dict(todo.metadata.items())
            del metadata["start"]
            desc = drop_word_if_startswith(todo.desc, "start:")
            return todo.new(desc=desc, metadata=metadata)
        else:
            return todo

    if start:
        return todo

    now = dt.datetime.now()
    start = f"{now.hour:0>2}{now.minute:0>2}"

    metadata = dict(todo.metadata.items())
    metadata["start"] = start
    desc = todo.desc + f" start:{start}"

    return todo.new(desc=desc, metadata=metadata)


###############################################################################
# Lastly, all POST todo spells are cast...
###############################################################################
@post_todo_spell
def remove_priorities(todo: T) -> T:
    """Remove priorities for done todos."""
    if todo.priority == magodo.DEFAULT_PRIORITY:
        return todo

    if not todo.done:
        return todo

    priority = magodo.DEFAULT_PRIORITY
    desc = drop_word_from_desc(todo.desc, f"({todo.priority})")
    return todo.new(desc=desc, priority=priority)
