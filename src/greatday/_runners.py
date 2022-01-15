"""Contains this project's clack runners.."""

from __future__ import annotations

from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._config import AddConfig, StartConfig
from ._repo import GreatDayRepo
from ._todo import InboxTodo


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    del cfg
    return 0


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    inbox_txt = cfg.data_dir / "todos" / "inbox.txt"
    inbox_repo: GreatDayRepo[InboxTodo] = GreatDayRepo(cfg.data_dir, inbox_txt)
    todo = InboxTodo.from_line(cfg.todo_line).unwrap()

    key = inbox_repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
