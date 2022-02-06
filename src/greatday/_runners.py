"""Contains this project's clack runners."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger
from vimala import vim

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo
from ._todo import GreatTodo


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    today = dt.date.today()
    daily_txt = cfg.data_dir / "daily.txt"

    todo_txts: list[Path] = []
    month = today.month
    for _ in range(3):
        todo_txt = cfg.data_dir / f"todos/{today.year}/{month:0>2}.txt"
        if todo_txt.is_file():
            todo_txts.append(todo_txt)
        month = last_month(month)

    vim_popen = vim(daily_txt, *todo_txts)
    vim_popen.communicate()

    return vim_popen.returncode


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
    repo = GreatRepo(todo_dir, GreatTodo)
    todo = GreatTodo.from_line(cfg.todo_line).unwrap()
    if "inbox" not in todo.contexts:
        contexts = list(todo.contexts) + ["inbox"]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
