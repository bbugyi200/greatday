"""Tests for the GreatSession potoroo.UnitOfWork class."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Final

import metaman
from pytest import mark

from greatday._repo import SQLRepo
from greatday._session import GreatSession
from greatday._tag import GreatTag

from . import common as c


params = mark.parametrize

FakeUserValidator = Callable[[SQLRepo], bool]
FakeEditorUser = Callable[[Path], FakeUserValidator]
FAKE_EDITOR_USERS: list[FakeEditorUser] = []
fake_editor_user = metaman.register_function_factory(FAKE_EDITOR_USERS)


@fake_editor_user
def delete_one_todo(path: Path) -> FakeUserValidator:
    """Deletes one todo from the file."""
    ID: Final = "1"

    lines = path.read_text().split("\n")
    new_text = "\n".join(line for line in lines if f" id:{ID}" not in line)
    path.write_text(new_text)

    def validator(repo: SQLRepo) -> bool:
        assert len(repo.all().unwrap()) == len(c.TODO_LINES) - 1
        assert repo.get(ID).unwrap() is None
        return True

    return validator


@fake_editor_user
def add_one_todo(path: Path) -> FakeUserValidator:
    """Adds one new todo to file."""
    ID: Final = str(int(c.TODO_LINE_IDS[-1]) + 1)
    DESC: Final = "NEW TODO"

    with path.open("a") as f:
        f.write(f"o {DESC}\n")

    def validator(repo: SQLRepo) -> bool:
        assert len(repo.all().unwrap()) == len(c.TODO_LINES) + 1
        todo = repo.get(ID).unwrap()
        assert todo is not None
        assert DESC in todo.to_line()
        return True

    return validator


@fake_editor_user
def edit_one_todo(path: Path) -> FakeUserValidator:
    """Edits one todo in file."""
    ID: Final = "1"
    CTX: Final = "ONE"

    lines = path.read_text().split("\n")
    new_lines: list[str] = []
    old_todo_line: str | None = None
    for line in lines:
        if f" id:{ID}" in line:
            old_todo_line = line
            new_lines.append(line + f" @{CTX}")
        else:
            new_lines.append(line)

    path.write_text("\n".join(new_lines))

    def validator(repo: SQLRepo) -> bool:
        todo = repo.get(ID).unwrap()
        assert todo is not None
        assert f" @{CTX} " in todo.desc
        assert CTX in todo.contexts
        assert old_todo_line is not None
        assert todo.to_line().replace(f" @{CTX}", "") == old_todo_line
        return True

    return validator


@params("faker", FAKE_EDITOR_USERS)
def test_fake_editor_users(sql_repo: SQLRepo, faker: FakeEditorUser) -> None:
    """Tests all fake editor user functions registered above."""
    tag = GreatTag.from_query("")
    with GreatSession(sql_repo.url, tag) as session:
        validator = faker(session.path)
        session.commit()
        assert validator(sql_repo)
