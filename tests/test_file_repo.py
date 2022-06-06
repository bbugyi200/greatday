"""Tests for greatday's FileRepo class."""

from __future__ import annotations

from pathlib import Path

from pytest import fixture

from greatday._repo import FileRepo
from greatday._todo import GreatTodo


TODO_LINES: list[str] = [
    "o foo | id:1",
    "o bar | id:2",
    "o baz | id:3",
]


@fixture(name="repo")
def file_repo_fixture(tmp_path: Path) -> FileRepo:
    """Returns a FileRepo populated with dummy data."""
    todo_file = tmp_path / "todos.txt"
    repo = FileRepo(todo_file)
    for line in TODO_LINES:
        todo = GreatTodo.from_line(line).unwrap()
        repo.add(todo).unwrap()
    return repo


def test_add_and_get(repo: FileRepo) -> None:
    """Tests the FileRepo's add() and get() methods."""
    assert len(repo.all().unwrap()) == len(TODO_LINES)

    ID = "100"
    todo = GreatTodo.from_line(f"o new todo | id:{ID}").unwrap()
    repo.add(todo).unwrap()
    assert len(repo.all().unwrap()) == len(TODO_LINES) + 1

    new_todo = repo.get(ID).unwrap()
    assert new_todo == todo


def test_remove(repo: FileRepo) -> None:
    """Tests the FileRepo.remove() method."""
    ID = "1"
    removed_todo = repo.remove(ID).unwrap()
    all_todos = repo.all().unwrap()
    assert len(all_todos) == len(TODO_LINES) - 1
    assert removed_todo not in all_todos
