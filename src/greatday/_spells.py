"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

import datetime as dt
from typing import Final, List

from eris import ErisResult, Ok
from magodo import Todo
from magodo.spells import register_spell_factory
from magodo.types import TodoSpell


TO_INBOX_SPELLS: List[TodoSpell] = []
to_inbox_spell = register_spell_factory(TO_INBOX_SPELLS)

TO_DAILY_SPELLS: List[TodoSpell] = []
to_daily_spell = register_spell_factory(TO_DAILY_SPELLS)

O_PREFIX: Final = "o "


@to_inbox_spell
def add_inbox_ctx(todo: Todo) -> ErisResult[Todo]:
    """Adds the @inbox context to the Todo."""
    if "inbox" in todo.contexts:
        return Ok(todo)

    contexts = todo.contexts + ("inbox",)
    return Ok(todo.new(contexts=contexts))


@to_inbox_spell
def add_create_date(todo: Todo) -> ErisResult[Todo]:
    """Adds today's date as the create date for this Todo."""
    if todo.create_date is not None:
        return Ok(todo)

    today = dt.date.today()
    return Ok(todo.new(create_date=today))


@to_inbox_spell
def add_ctime(todo: Todo) -> ErisResult[Todo]:
    """Adds creation time to Todo via the 'ctime' metadata tag."""
    if "ctime" in todo.metadata:
        return Ok(todo)

    now = dt.datetime.now()

    metadata = dict(todo.metadata)
    metadata["ctime"] = f"{now.hour:0>2}{now.minute:0>2}"

    return Ok(todo.new(metadata=metadata))


@to_daily_spell
def add_o_prefix(todo: Todo) -> ErisResult[Todo]:
    """Adds the 'o ' prefix to the Todo's description."""
    if todo.desc.startswith(O_PREFIX):
        return Ok(todo)

    desc = O_PREFIX + todo.desc
    return Ok(todo.new(desc=desc))
