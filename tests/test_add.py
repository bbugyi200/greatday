"""Test for greatday's 'add' subcommand."""

from __future__ import annotations

from .conftest import MainType


def test_add(main: MainType) -> None:
    """Tests the 'add' subcommand."""
    assert main("add", "foo") == 0
