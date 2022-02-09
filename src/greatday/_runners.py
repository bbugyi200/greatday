"""Contains this project's clack runners."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Callable, Iterable, List

import clack
from clack.types import ClackRunner
from ion import getch
from logrus import Logger
import magodo
from typist import assert_never
from vimala import vim

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo, Tag
from ._session import GreatSession
from ._todo import GreatTodo
from .types import YesNoPrompt


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    todo_dir = cfg.data_dir / "todos"
    with GreatSession(
        todo_dir, Tag(contexts=["inbox"]), name="inbox"
    ) as session:
        inbox_todos = list(session.repo.todo_group)
        vim(session.path).unwrap()
        commit_todo_changes(
            session, old_todos=inbox_todos, commit_mode=cfg.commit_mode
        )

    today = dt.date.today()
    with GreatSession(
        todo_dir,
        Tag(metadata_checks={"tickle": tickle_check(today)}),
        name="ticklers",
    ) as session:
        tickler_todos = list(session.repo.todo_group)
        vim(session.path).unwrap()
        commit_todo_changes(
            session, old_todos=tickler_todos, commit_mode=cfg.commit_mode
        )

    today = dt.date.today()
    daily_txt = cfg.data_dir / "daily.txt"

    todo_txts: list[Path] = []
    month = today.month
    year = today.year
    for _ in range(36):
        todo_txt = todo_dir / f"{year}/{month:0>2}.txt"
        if todo_txt.is_file():
            todo_txts.append(todo_txt)

        if month == 1:
            year -= 1

        month = last_month(month)

    proc = vim(daily_txt, *todo_txts).unwrap()
    return proc.popen.returncode


def commit_todo_changes(
    session: GreatSession,
    *,
    old_todos: Iterable[GreatTodo],
    commit_mode: YesNoPrompt = "prompt",
) -> None:
    """Commit todo changes to disk."""
    for otodo in old_todos:
        key = otodo.ident

        new_todo = session.repo.get(key).unwrap()
        if otodo != new_todo:
            break
    else:
        return

    should_commit: bool
    if commit_mode == "y":
        should_commit = True
    elif commit_mode == "n":
        should_commit = False
    elif commit_mode == "prompt":
        should_commit = bool(
            getch("Commit these todo changes? (y/n): ") == "y"
        )
    else:
        assert_never(commit_mode)

    if should_commit:
        session.commit()
    else:
        session.rollback()


def tickle_check(today: dt.date) -> Callable[[str], bool]:
    """Returns MetadataChecker that returns all due ticklers."""

    def check(tickle_value: str) -> bool:
        due_date = magodo.to_date(tickle_value)
        return due_date <= today

    return check


def last_month(month: int) -> int:
    """Returns the int month before `month`."""
    assert 1 <= month <= 12
    if month == 1:
        return 12
    else:
        return month - 1


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    todo_dir = cfg.data_dir / "todos"
    repo = GreatRepo(todo_dir)
    todo = GreatTodo.from_line(cfg.todo_line).unwrap()
    if cfg.add_inbox_context and "inbox" not in todo.contexts:
        contexts = list(todo.contexts) + ["inbox"]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
