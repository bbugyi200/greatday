"""Contains this project's clack runners."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List

import clack
from clack.types import ClackRunner
from ion import getch
from logrus import Logger
from vimala import vim

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo, Tag
from ._session import GreatSession
from ._todo import GreatTodo


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    todo_dir = cfg.data_dir / "todos"
    with GreatSession(todo_dir) as session:
        inbox_todos = session.repo.get_by_tag(Tag(contexts=["inbox"])).unwrap()
        contents = [todo.to_line() for todo in inbox_todos]
        session.path.write_text(
            "\n".join(contents)
        )

        V = vim(session.path)
        V.communicate()

        if getch("commit these todo changes? (y/n): ") == "y":
            session.commit()
        else:
            session.rollback()

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

    V = vim(daily_txt, *todo_txts)
    V.communicate()

    return V.returncode


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
    if "inbox" not in todo.contexts:
        contexts = list(todo.contexts) + ["inbox"]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
