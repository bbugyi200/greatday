"""Test for greatday's 'list' subcommand."""

from __future__ import annotations

from _pytest.capture import CaptureFixture
from pytest import mark

from greatday._repo import SQLRepo

from . import common


params = mark.parametrize


@params("query,expected_ids", common.QUERY_TO_TODO_IDS)
def test_list(
    capsys: CaptureFixture,
    main: common.MainType,
    sql_repo: SQLRepo,
    query: str,
    expected_ids: list[int],
) -> None:
    """Tests the 'list' subcommand."""
    del sql_repo

    assert main("list", query) == 0
    captured = capsys.readouterr()
    id_list: list[int] = []
    for line in captured.out.split("\n"):
        line = line.strip()
        for word in line.split(" "):
            if word.startswith("id:"):
                _, ID = word.split(":")
                id_list.append(int(ID))

    id_list.sort()
    expected_ids.sort()
    assert id_list == expected_ids
