"""Test for greatday's 'add' subcommand."""

from __future__ import annotations

from pathlib import Path

from .conftest import MainType


def test_add(main: MainType, tmp_path: Path) -> None:
    """Tests the 'add' subcommand."""
    data_dir = tmp_path / "data"
    assert main("add", "foo", data_dir=data_dir) == 0
