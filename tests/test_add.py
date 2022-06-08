"""Test for greatday's 'add' subcommand."""

from __future__ import annotations

from . import common as c


def test_add(main: c.MainType) -> None:
    """Tests the 'add' subcommand."""
    assert main("add", "foo") == 0
