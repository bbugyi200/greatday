"""Tests for greatday's Repo classes."""

from __future__ import annotations

import warnings

from pytest import fixture, mark

from greatday import db
from greatday._repo import SQLRepo
from greatday._todo import GreatTodo


params = mark.parametrize

TODO_LINES = [
    "o 2000-01-01 Do Laundry | @home",
    "o 2000-02-03 Buy groceries | @out +buy due:2000-02-03",
    "x 2000-01-02 2000-01-01 Finish greatday tests | @dev +greatday",
]


@fixture(name="sql_repo")
def sql_repo_fixture() -> SQLRepo:
    """Returns a SQLRepo populated with dummy data."""
    # The following line is necessary so we get a new DB instance everytime
    # this fixture is used.
    db.cached_engine.cache_clear()

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


@params("key", ["1", "2", "3"])
def test_sql_get_and_remove(sql_repo: SQLRepo, key: str) -> None:
    """Tests the SQLRepo.get() and SQLRepo.remove() methods."""
    todo = sql_repo.get(key).unwrap()
    assert todo == sql_repo.remove(key).unwrap()
    assert len(TODO_LINES) == len(sql_repo.all().unwrap()) + 1
