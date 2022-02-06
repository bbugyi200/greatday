"""Contains this project's clack runners."""

from __future__ import annotations

from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._config import AddConfig
from ._repo import GreatRepo
from ._todo import ToInboxTodo


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    todo_dir = cfg.data_dir / "todos"
    repo = GreatRepo(todo_dir, ToInboxTodo)
    todo = ToInboxTodo.from_line(cfg.todo_line).unwrap()

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
