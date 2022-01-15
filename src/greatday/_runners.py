"""Contains this project's clack runners.."""

from __future__ import annotations

from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo
from ._todo import InboxTodo


ALL_RUNNERS: List[ClackRunner] = []
register_runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@register_runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    del cfg
    return 0


@register_runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    repo: GreatRepo[InboxTodo] = GreatRepo(cfg.data_dir)
    todo = InboxTodo.from_line(cfg.todo_line).unwrap()

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
