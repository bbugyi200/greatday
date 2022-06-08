"""Test for greatday's 'add' subcommand."""

from __future__ import annotations

from . import common


def test_add(main: common.MainType) -> None:
    """Tests the 'add' subcommand."""
    assert main("add", "foo") == 0
