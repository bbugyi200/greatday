"""Tests for greatday magodo spells."""

from __future__ import annotations

from eris import Err
from pytest import mark

from greatday._todo import GreatTodo

from . import common as c


params = mark.parametrize


@params(
    "in_line, out_line",
    [
        # --- x_points spell
        (
            "x:1 foo",
            f"x:{c.hhmm} {c.TODAY} {c.TODAY} foo | ctime:{c.hhmm} p:1",
        ),
        (
            "x:1 2022-06-07 foo",
            f"x:{c.hhmm} {c.TODAY} 2022-06-07 foo | ctime:{c.hhmm} p:1",
        ),
        (
            "x:1 2022-06-07 2022-06-06 foo",
            f"x:{c.hhmm} 2022-06-07 2022-06-06 foo | ctime:{c.hhmm} p:1",
        ),
        # --- snooze spell
        (
            "o foo snooze:1d",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:{c.TOMORROW}",
        ),
        (
            f"(P) foo due:{c.TODAY} snooze:1d",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:{c.TOMORROW}",
        ),
        (
            f"o foo due:{c.TODAY} s:1d",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:{c.TOMORROW}",
        ),
        # --- relative dates spell
        (
            "o foo due:0d",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:{c.TODAY}",
        ),
        (
            "o foo due:1d",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:{c.TOMORROW}",
        ),
        # --- due context spell
        (
            "o foo @due",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:{c.TODAY}",
        ),
        # --- appt spell
        (
            "o foo appt:0100",
            f"o {c.TODAY} foo | appt:0100 ctime:{c.hhmm}",
        ),
        (
            f"o foo due:{c.TODAY} appt:0100",
            f"(T) {c.TODAY} foo | appt:0100 ctime:{c.hhmm} due:{c.TODAY}",
        ),
        (
            f"o foo due:{c.TODAY} appt:0030",
            f"(C) {c.TODAY} foo | appt:0030 ctime:{c.hhmm} due:{c.TODAY}",
        ),
        # --- in-progress priority spell
        (
            "(D) foo",
            f"(D) {c.TODAY} foo | ctime:{c.hhmm} start:{c.hhmm}",
        ),
        (
            "o foo start:1234",
            f"o {c.TODAY} foo | ctime:{c.hhmm}",
        ),
    ],
)
def test_spells(in_line: str, out_line: str) -> None:
    """Tests intended to flex greatday's custom magodo spells."""
    todo_result = GreatTodo.from_line(in_line)
    assert not isinstance(todo_result, Err)

    todo = todo_result.ok()
    assert todo.to_line() == out_line
