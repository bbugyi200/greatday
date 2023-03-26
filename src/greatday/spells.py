"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

import datetime as dt
from typing import Callable, Final, Iterable, List

from logrus import Logger
import magodo
from magodo.types import LineSpell, Metadata, T, TodoSpell
from metaman import register_function_factory

from .common import drop_word_if_startswith, drop_words, todo_prefixes
from .dates import (
    RELATIVE_DATE_METATAGS,
    SUNDAY,
    dt_from_date_and_hhmm,
    get_all_days,
    get_month_days,
    get_next_day,
    get_quarter_days,
    get_relative_date,
    matches_date_fmt,
    matches_relative_date_fmt,
)


logger = Logger(__name__)

# priority that indicates that a todo is "in progress"
IN_PROGRESS_PRIORITY: Final = "D"

# initialize decorators to register spell functions
GREAT_PRE_TODO_SPELLS: List[TodoSpell] = []
pre_todo_spell = register_function_factory(GREAT_PRE_TODO_SPELLS)

GREAT_TODO_SPELLS: List[TodoSpell] = []
todo_spell = register_function_factory(GREAT_TODO_SPELLS)

GREAT_POST_TODO_SPELLS: List[TodoSpell] = []
post_todo_spell = register_function_factory(GREAT_POST_TODO_SPELLS)

GREAT_TO_LINE_SPELLS: List[LineSpell] = []
to_line_spell = register_function_factory(GREAT_TO_LINE_SPELLS)

GREAT_FROM_LINE_SPELLS: List[LineSpell] = []
from_line_spell = register_function_factory(GREAT_FROM_LINE_SPELLS)


###############################################################################
# pre-todo spells | First, all PRE todo spells are cast...
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
    desc_words = desc.split(" ")
    desc_words.pop(0)  # x:HHMM

    if matches_date_fmt(desc_words[0]):
        create_date = magodo.dates.to_date(desc_words.pop(0))
    else:
        create_date = None

    if matches_date_fmt(desc_words[0]):
        done_date = create_date
        create_date = magodo.dates.to_date(desc_words.pop(0))
    else:
        done_date = None

    desc = " ".join(desc_words) + f" p:{points}"

    return todo.new(
        create_date=create_date,
        desc=desc,
        done=True,
        done_date=done_date,
        metadata=metadata,
    )


###############################################################################
# normal todo spells | Then all NORMAL todo spells are cast...
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
    metadata: Metadata | None = {}

    for key in RELATIVE_DATE_METATAGS:
        value = todo.metadata.get(key)
        if not value:
            continue

        if not matches_relative_date_fmt(value):
            continue

        # we only create a new dict of metadata if we have to
        if not found_tag:
            found_tag = True
            metadata = dict(todo.metadata.items())

        value_date = get_relative_date(value)
        new_value = magodo.dates.from_date(value_date)

        assert metadata is not None
        metadata[key] = new_value

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
    desc = drop_words(todo.desc, "@due")
    metadata = dict(todo.metadata.items())
    metadata["due"] = magodo.dates.from_date(today)
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
    if magodo.dates.to_date(due) > today:
        return todo

    now = dt.datetime.now()
    appt_dt = dt_from_date_and_hhmm(today, appt)
    if appt_dt < now + dt.timedelta(hours=1):
        priority = "C"
    else:
        priority = "T"

    return todo.new(priority=priority)


@todo_spell
def inbox_spell(todo: T) -> T:
    """Converts @i into @INBOX."""
    if "i" not in todo.contexts:
        return todo
    contexts = [ctx for ctx in todo.contexts if ctx != "i"]
    contexts.append("INBOX")
    return todo.new(contexts=contexts)


@todo_spell
def scope_spell(todo: T) -> T:
    """Spell that handles @w/@m/@q/@y/@o/@t/@s contexts.

    Adds appropriate 'scope' metatag and 'due' date.
    """
    day_of_week = SUNDAY

    def get_w_due() -> dt.date:
        return get_next_day(day_of_week=day_of_week)

    def get_m_due() -> dt.date:
        return get_next_day(day_of_week=day_of_week, day_maker=get_month_days)

    def get_q_due() -> dt.date:
        return get_next_day(
            day_of_week=day_of_week, day_maker=get_quarter_days
        )

    def get_y_due() -> dt.date:
        year = dt.date.today().year + 1
        return get_all_days(day_of_week=day_of_week, year=year)[0]

    def get_o_due() -> dt.date:
        return get_next_nth_year_day(4)

    def get_t_due() -> dt.date:
        return get_next_nth_year_day(20)

    def get_next_nth_year_day(n: int) -> dt.date:
        d = dt.date.today()
        y = d.year + 1
        while y % n != 0:
            y += 1
        return get_all_days(day_of_week=day_of_week, year=y)[0]

    scope_contexts = ["w", "m", "q", "y", "o", "t", "s"]
    get_due_funcs: list[Callable[[], dt.date | None]] = [
        get_w_due,
        get_m_due,
        get_q_due,
        get_y_due,
        get_o_due,
        get_t_due,
        lambda: None,
    ]

    scope: int | None = None
    due: dt.date | None = None
    for i, (ctx, get_due) in enumerate(
        zip(
            scope_contexts,
            get_due_funcs,
        )
    ):
        if ctx in todo.contexts:
            scope = i + 1
            due = get_due()
            break
    else:
        return todo

    assert scope is not None

    todo = reopen_if_closed(todo)
    bad_contexts = scope_contexts + ["INBOX"]
    contexts = [ctx for ctx in todo.contexts if ctx not in bad_contexts]

    metadata = dict(todo.metadata.items())
    metadata["scope"] = str(scope)
    if due is not None:
        metadata["due"] = magodo.dates.from_date(due)
    elif "due" in metadata:
        del metadata["due"]

    return todo.new(contexts=contexts, metadata=metadata)


@todo_spell
def reopen_todo_spell(todo: T) -> T:
    """Spell that re-opens todos when the '@x' context is found."""
    if "x" not in todo.contexts:
        return todo

    todo = reopen_if_closed(todo)
    contexts = [ctx for ctx in todo.contexts if ctx != "x"]
    return todo.new(contexts=contexts)


def reopen_if_closed(todo: T) -> T:
    """Re-opens a closed todo."""
    if not todo.done:
        return todo

    metadata = dict(todo.metadata.items())
    if "dtime" in metadata:
        del metadata["dtime"]

    return todo.new(done=False, done_date=None, metadata=metadata)


###############################################################################
# post-todo spells | Lastly, all POST todo spells are cast...
###############################################################################
@post_todo_spell
def remove_priorities(todo: T) -> T:
    """Remove priorities for done todos."""
    if todo.priority == magodo.DEFAULT_PRIORITY:
        return todo

    if not todo.done:
        return todo

    priority = magodo.DEFAULT_PRIORITY
    desc = drop_words(todo.desc, f"({todo.priority})")
    return todo.new(desc=desc, priority=priority)


@post_todo_spell
def group_tags(todo: T) -> T:
    """Spell that organizes Todo tags by grouping them at the end.

    Groups all #epics, @ctxs, +projs, and meta:data at the end of the line.
    """
    if not (todo.epics or todo.contexts or todo.projects or todo.metadata):
        return todo

    def all_words_are_tags(words: Iterable[str]) -> bool:
        """Returns True if all `words` are special words."""
        return all(magodo.tags.is_any_tag(w) for w in words)

    all_words = [w for w in todo.desc.split(" ") if w != "|"]
    regular_words: list[str] = []
    for i, word in enumerate(all_words[:]):
        if not word:
            continue

        all_prev_words_are_tags = all_words_are_tags(all_words[:i])
        all_next_words_are_tags = all_words_are_tags(all_words[i + 1 :])
        is_edge_tag = all_next_words_are_tags or all_prev_words_are_tags

        if (
            magodo.tags.is_metadata_tag(word)
            and word[-1] in magodo.PUNCTUATION
        ):
            return todo

        if magodo.tags.is_any_prefix_tag(word) and (
            word[-1] in magodo.PUNCTUATION or not all_next_words_are_tags
        ):
            if regular_words:
                regular_words.append(word[1:])
            continue

        if magodo.tags.is_any_prefix_tag(word) and is_edge_tag:
            continue

        if magodo.tags.is_metadata_tag(word):
            continue

        regular_words.append(word)

    desc = " ".join(regular_words).strip()
    space = ""
    if regular_words:
        desc += " |"
        space = " "

    if todo.epics:
        desc += space + " ".join(
            magodo.tags.EPIC_PREFIX + epic for epic in sorted(todo.epics)
        )
        space = " "

    if todo.contexts:
        desc += space + " ".join(
            magodo.tags.CONTEXT_PREFIX + ctx for ctx in sorted(todo.contexts)
        )
        space = " "

    if todo.projects:
        desc += space + " ".join(
            magodo.tags.PROJECT_PREFIX + ctx for ctx in sorted(todo.projects)
        )
        space = " "

    if todo.metadata:
        desc += space + " ".join(
            f"{k}:{v}" for (k, v) in sorted(todo.metadata.items())
        )
        space = " "

    return todo.new(desc=desc)


###############################################################################
# to-line spells | Called on lines produced by `Todo.to_line()`
###############################################################################
@to_line_spell
def add_o_prefix(line: str) -> str:
    """Adds the 'o ' prefix to the Todo line."""
    if line.startswith(todo_prefixes()):
        return line

    return "o " + line


@to_line_spell
def add_x_prefix(line: str) -> str:
    """Adds the 'x:HHMM ' prefix to the Todo line (when done)."""
    if not line.startswith("x "):
        return line

    words = line.split(" ")[1:]
    for i, word in enumerate(words[:]):
        if word.startswith("dtime:"):
            del words[i]
            dtime = word.split(":")[1]
            break
    else:
        return line

    rest = " ".join(words)
    return f"x:{dtime} {rest}"


###############################################################################
# from-line spells | Called on lines consumed by `Todo.from_line()`
###############################################################################
@from_line_spell
def remove_o_prefix(line: str) -> str:
    """Removes the 'o ' prefix from the Todo line."""
    if not line.startswith("o "):
        return line

    return line[len("o ") :]


@from_line_spell
def remove_x_prefix(line: str) -> str:
    """Removes the 'x:HHMM ' prefix from the Todo line."""
    if not line.startswith("x:"):
        return line

    xhhmm, *words = line.split(" ")
    dtime = xhhmm.split(":")[1]
    if len(dtime) != 4:
        return line

    rest = " ".join(words)
    return f"x {rest} dtime:{dtime}"
