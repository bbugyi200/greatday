"""Tests for greatday's SQLRepo class."""

from __future__ import annotations

from pytest import fixture, mark

from greatday import db
from greatday._repo import SQLRepo
from greatday._tag import GreatTag
from greatday._todo import GreatTodo

from . import common


params = mark.parametrize


@fixture(name="repo")
def sql_repo_fixture() -> SQLRepo:
    """Returns a SQLRepo populated with dummy data."""
    repo = SQLRepo("sqlite://", engine_factory=db.create_engine)
    for line in common.TODO_LINES:
        todo = GreatTodo.from_line(line).unwrap()
        repo.add(todo).unwrap()
    return repo


def test_add(repo: SQLRepo) -> None:
    """Tests the SQLRepo.add() method.

    NOTE: Nothing needs to be done here since the repo fixture invokes the
    SQLRepo.add() method for us.
    """
    assert len(common.TODO_LINES) == len(repo.all().unwrap())


@params("key", common.TODO_LINE_IDS)
def test_get_and_remove(repo: SQLRepo, key: str) -> None:
    """Tests the SQLRepo.get() and SQLRepo.remove() methods."""
    todo = repo.get(key).unwrap()
    assert todo == repo.remove(key).unwrap()
    assert len(common.TODO_LINES) == len(repo.all().unwrap()) + 1


@params("key", common.TODO_LINE_IDS)
def test_update(repo: SQLRepo, key: str) -> None:
    """Tests the SQLRepo.update() method."""
    old_todo = GreatTodo.from_line(
        common.TODO_LINES[int(key) - 1] + f" id:{key}"
    ).unwrap()
    todo = GreatTodo.from_line(f"o foobar @foo @bar id:{key}").unwrap()

    actual_old_todo = repo.update(key, todo).unwrap()
    assert old_todo == actual_old_todo

    actual_todo = repo.get(key).unwrap()
    assert todo == actual_todo


@params("query,keys", common.QUERY_TO_TODO_IDS)
def test_get_by_tag(repo: SQLRepo, query: str, keys: list[str]) -> None:
    """Tests the SQLRepo.get_by_tag() method."""
    tag = GreatTag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()
    assert sorted(todo.ident for todo in todos) == sorted(str(k) for k in keys)


def test_remove_by_tag(repo: SQLRepo) -> None:
    """Tests the SQLRepo.remove_by_tag() method."""
    CTX = "@dev"
    matched_line_count = len(
        [line for line in common.TODO_LINES if CTX in line.split(" ")]
    )
    tag = GreatTag.from_query(CTX)
    removed_todos = repo.remove_by_tag(tag).unwrap()
    assert len(removed_todos) == matched_line_count
    assert (
        len(repo.all().unwrap()) == len(common.TODO_LINES) - matched_line_count
    )
