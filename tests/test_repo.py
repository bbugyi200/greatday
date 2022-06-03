"""Tests for greatday's Repo classes."""

from __future__ import annotations

import warnings

from pytest import fixture

from greatday._repo import SQLRepo
from greatday._todo import GreatTodo


TODO_LINES = [
    "o 2000-01-01 Do Laundry | @home",
    "o 2000-02-03 Buy groceries | @out +buy due:2000-02-03",
    "x 2000-01-02 2000-01-01 Finish greatday tests | @dev +greatday",
]


@fixture(name="sql_repo")
def sql_repo_fixture() -> SQLRepo:
    """Returns a SQLRepo populated with dummy data."""
    # HACK: see https://github.com/tiangolo/sqlmodel/issues/189
    warnings.filterwarnings(
        "ignore",
        ".*Class SelectOfScalar will not make use of SQL compilation"
        " caching.*",
    )
    sql_repo = SQLRepo("sqlite://")
    for line in TODO_LINES:
        todo = GreatTodo.from_line(line).unwrap()
        sql_repo.add(todo).unwrap()
    return sql_repo


def test_sql_add(sql_repo: SQLRepo) -> None:
    """Tests the SQLRepo.add() method.

    NOTE: Nothing needs to be done here since the sql_repo fixture invokes the
    SQLRepo.add() method for us.
    """
    assert len(TODO_LINES) == len(sql_repo.all().unwrap())
