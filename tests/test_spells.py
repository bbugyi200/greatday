"""Tests for greatday magodo spells."""

from __future__ import annotations

from eris import Err
from pytest import mark

from greatday.todo import GreatTodo

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
            f"o foo due:{c.TODAY} appt:0200",
            f"(T) {c.TODAY} foo | appt:0200 ctime:{c.hhmm} due:{c.TODAY}",
        ),
        (
            f"o foo due:{c.TODAY} appt:0100",
            f"(C) {c.TODAY} foo | appt:0100 ctime:{c.hhmm} due:{c.TODAY}",
        ),
        # --- scope spell
        (
            "o foo @w",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:2000-01-10 scope:1",
        ),
        (
            "o foo scope:1 @m",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:2000-01-31 scope:2",
        ),
        (
            "o foo scope:4 @q",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:2000-04-03 scope:3",
        ),
        (
            "o foo @y",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:2001-01-01 scope:4",
        ),
        (
            "o foo scope:4 @o",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:2004-01-05 scope:5",
        ),
        (
            "o foo scope:4 @t",
            f"o {c.TODAY} foo | ctime:{c.hhmm} due:2020-01-06 scope:6",
        ),
        (
            "o foo scope:5 due:2020-01-06 @s",
            f"o {c.TODAY} foo | ctime:{c.hhmm} scope:7",
        ),
        (
            f"x {c.TODAY} 2023-03-04 foo @w",
            f"o 2023-03-04 foo | ctime:{c.hhmm} due:2000-01-10 scope:1",
        ),
        (
            f"o 2023-03-04 foo @INBOX @w",
            f"o 2023-03-04 foo | ctime:{c.hhmm} due:2000-01-10 scope:1",
        ),
        # --- inbox spell
        ("o foo @i", f"o {c.TODAY} foo | @INBOX ctime:{c.hhmm}"),
        # --- reopen spell
        (
            f"x:1234 {c.TODAY} 2023-03-04 foo @x",
            f"o 2023-03-04 foo | ctime:{c.hhmm}",
        ),
        (
            "o 2023-03-04 foo @x",
            f"o 2023-03-04 foo | ctime:{c.hhmm}",
        ),
    ],
)
def test_spells(in_line: str, out_line: str) -> None:
    """Tests intended to flex greatday's custom magodo spells."""
    todo_result = GreatTodo.from_line(in_line)
    assert not isinstance(todo_result, Err)

    todo = todo_result.ok()
    assert todo.to_line() == out_line
