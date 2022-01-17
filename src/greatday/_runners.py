"""Contains this project's clack runners.."""

from __future__ import annotations

from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo
from ._todo import ToInboxTodo


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    del cfg
    # If any Todos exist with a priority of 'C' or higher...
    # Process them first...

    # How many days (N) has it been since ticklers were checked?

    # If we didn't check ticklers yet today (i.e. N > 0)...
    # Process last N days of ticklers...

    # If daily backup file already exists...
    # Ask the user: Can we delete this backup file?

    # Process all @inbox Todos.

    # Clear daily file of all done Todos.

    ### START: Daily Todo Collection
    # Collect all Todos in daily file.
    #
    # Collect all Todos with priority greater than or equal to 'D'.
    #
    # Prompt the user for more Todos (using fuzzy matching).
    ### END: Daily Todo Collection

    # Render / format the daily file using the Todos we collected.

    # Copy the daily file to the backup daily file.

    # Use vimlala to open daily file in vim.

    # Collect Todos from daily file.

    # Run tests on all collected daily file Todos.

    # For each failed test...
    # Prompt the user for a fix.

    # Ask the user: Can we commit / save the daily file?
    # Copy the contents of the backup daily file to the daily file.
    # Delete the backup daily file.
    return 0


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    inbox_txt = cfg.data_dir / "todos" / "inbox.txt"
    inbox_repo: GreatRepo[ToInboxTodo] = GreatRepo(cfg.data_dir, inbox_txt)
    todo = ToInboxTodo.from_line(cfg.todo_line).unwrap()

    key = inbox_repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
