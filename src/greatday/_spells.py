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

from ._common import CTX_TODAY, drop_word_from_desc
from ._dates import (
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
    make_new_todo = False
    metadata = dict(todo.metadata.items())
    s = metadata.get("s")
    if s is not None:
        metadata["snooze"] = s
        del metadata["s"]
        make_new_todo = True

    snooze = metadata.get("snooze")
    if snooze is None:
        return todo

    desc = drop_word_if_startswith(todo.desc, "snooze:")

    today = dt.date.today()

    if matches_date_fmt(snooze):
        snooze_date = magodo.to_date(snooze)
    else:
        snooze_date = get_relative_date(snooze)

    desc = todo.desc

    if snooze_date <= today:
        del metadata["snooze"]
        return todo.new(desc=todo.desc, metadata=metadata)
    elif make_new_todo:
        return todo.new(desc=desc, metadata=metadata)
    else:
        return todo


@todo_spell
def render_relative_dates(todo: T) -> T:
    """Renders metatags that support relative dates.

    (e.g. 'tickle:1d' -> 'tickle:2022-02-16')
    """
    found_tag = False
    desc = todo.desc
    metadata = dict(todo.metadata.items())

    for key in ["snooze", "tickle", "until", "due"]:
        # t_or_s: Tickle or Snooze
        t_o_s = todo.metadata.get(key)
        if not t_o_s:
            continue

        if not matches_relative_date_fmt(t_o_s):
            continue

        found_tag = True

        new_t_or_s_date = get_relative_date(t_o_s)
        new_t_or_s = magodo.from_date(new_t_or_s_date)
        metadata[key] = new_t_or_s

        desc = drop_word_if_startswith(desc, key + ":")

    if not found_tag:
        return todo

    return todo.new(desc=desc, metadata=metadata)


@todo_spell
def due_context_spell(todo: T) -> T:
    """Converts @due context into today context."""
    if "due" not in todo.contexts:
        return todo

    contexts = [ctx for ctx in todo.contexts if ctx != "due"]
    contexts.append(CTX_TODAY)
    desc = drop_word_from_desc(todo.desc, "@due")
    return todo.new(desc=desc, contexts=contexts)


@todo_spell
def due_metatag_spell(todo: T) -> T:
    """Handles the 'due' metatag."""
    due = todo.metadata.get("due")
    if not due or not matches_date_fmt(due):
        return todo

    today = dt.date.today()
    due_date = magodo.to_date(due)
    if due_date <= today:
        metadata = dict(todo.metadata.items())
        recur = todo.metadata.get("recur")
        if not recur or recur.islower():
            del metadata["due"]

        contexts = list(todo.contexts)
        if CTX_TODAY not in contexts:
            contexts.append(CTX_TODAY)

        return todo.new(contexts=contexts, metadata=metadata)
    elif CTX_TODAY in todo.contexts:
        contexts = [ctx for ctx in todo.contexts if ctx != CTX_TODAY]
        return todo.new(contexts=contexts)

    return todo


@todo_spell
def handle_today_context(todo: T) -> T:
    """Handles the context tag that marks a todo as planned to be done today.

    By "handles", we mean that this spell makes sure that todos which should
    have the today context do and vice-versa.
    """
    if not todo.done_date:
        return todo

    today = dt.date.today()

    should_have_today_ctx = bool(
        todo.done_date == today
        and any(key in todo.metadata for key in ["p", "xp"])
    )
    has_today_ctx = bool(CTX_TODAY in todo.contexts)
    if has_today_ctx == should_have_today_ctx:
        return todo

    contexts = [ctx for ctx in todo.contexts if ctx != CTX_TODAY]
    if should_have_today_ctx:
        contexts.append(CTX_TODAY)

    return todo.new(contexts=contexts)


@todo_spell
def recur_tickler_spell(todo: T) -> T:
    """Handles the 'recur:' metatag for tickler todos."""
    mdata = todo.metadata

    if not todo.done_date:
        return todo

    recur = mdata.get("recur")
    if not recur:
        return todo

    tickle = mdata.get("tickle")
    if not tickle:
        return todo

    assert isinstance(recur, str)
    if recur.islower():
        start_date = todo.done_date
    else:
        start_date = magodo.to_date(tickle)

    until = mdata.get("until")
    if until and magodo.to_date(until) <= start_date:
        logger.debug("Recurring todo has reached its 'until' date.", todo=todo)
        return todo

    next_date = get_relative_date(recur, start_date=start_date)
    metadata = dict(mdata.items())

    if magodo.to_date(tickle) <= todo.done_date:
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
    """Adds priority of (C) or (T) to todos with an appt:HHMM tag."""
    appt = todo.metadata.get("appt")
    if not appt:
        return todo

    if todo.done or todo.done_date:
        return todo

    if CTX_TODAY not in todo.contexts:
        return todo

    today = dt.date.today()
    now = dt.datetime.now()
    appt_dt = dt_from_date_and_hhmm(today, appt)
    if appt_dt < now + dt.timedelta(minutes=30):
        priority = "C"
    else:
        priority = "T"

    return todo.new(priority=priority)


###############################################################################
# Lastly, all POST todo spells are cast...
###############################################################################
@post_todo_spell
def remove_priorities(todo: T) -> T:
    """Remove prioritis for done todos or non-today todos."""
    if todo.priority == magodo.DEFAULT_PRIORITY:
        return todo

    if not todo.done and CTX_TODAY in todo.contexts:
        return todo

    priority = magodo.DEFAULT_PRIORITY
    desc = drop_word_from_desc(todo.desc, f"({todo.priority})")
    return todo.new(desc=desc, priority=priority)
