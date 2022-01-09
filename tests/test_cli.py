"""Tests the greatday project's CLI."""

from __future__ import annotations

from greatday.cli import main


def test_main() -> None:
    """Tests main() function."""
    assert main([""]) == 0
