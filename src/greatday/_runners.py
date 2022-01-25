"""Contains this project's clack runners."""

from __future__ import annotations

from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    great_repo = GreatRepo(
        cfg.data_dir, writer=ToGreatTodo, reader=FromGreatTodo
    )
    inbox_repo = GreatRepo(
        cfg.data_dir, writer=ToInboxTodo, reader=FromInboxTodo
    )

    tag = lambda todo: todo.priority <= "C"
    high_priority_todos = great_repo.get_by_tag(tag).unwrap()

    process_great_todos = partial(process_repo_todos, great_repo)
    process_inbox_todos = partial(process_repo_todos, inbox_repo)

    # If any Todos exist with a priority of 'C' or higher...
    if high_priority_todos:
        # Process them first...
        process_great_todos(high_priority_todos)

    # How many days (N) has it been since ticklers were checked?
    N = days_since_ticklers_processed(cfg.data_dir)

    # If we didn't check ticklers yet today (i.e. N > 0)...
    if N > 0:
        # Process last N days of ticklers...
        today = dt.date.today()
        tag = (
            lambda todo: "tickle" in todo.projects
            and (today - to_date(todo.metadata["date"])).days < N
        )
        tickler_todos = great_repo.get_by_tag(tag).unwrap()
        process_great_todos(tickler_todos)

    # Process all @inbox Todos.
    tag = lambda todo: "inbox" in todo.contexts
    inbox_todos = great_repo.get_by_tag(tag).unwrap()
    process_inbox_todos(inbox_todos)

    # Prompt the user for an optional list of contexts.
    daily_contexts = input_daily_contexts()

    # Collect all Todos with priority equal to 'D'.
    tag = lambda todo: todo.priority == "D"
    d_priority_todos = great_repo.get_by_tag(tag).unwrap()

    # Prompt the user for more Todos (using fuzzy matching).
    user_selected_todos = []
    for tid in input_fuzzy_todos(cfg.data_dir):
        todo = great_repo.get(tid).unwrap()
        user_selected_todos.append(todo)

    # Process daily todos.
    daily_todos = []
    daily_todos.extend(d_priority_todos)
    daily_todos.extend(user_selected_todos)

    process_great_todos(daily_todos, contexts=daily_contexts)

    return 0


def process_repo_todos(repo, todos_to_process, *, contexts=None):
    with GreatSession(repo, todos_to_process, contexts=contexts) as session:
        if ion.getch("OK to commit these changes?: ") == "y":
            session.commit()
        else:
            session.rollback()


def days_since_ticklers_processed(data_dir):
    pass


def input_fuzzy_todos(data_dir):
    pass


def input_daily_contexts():
    pass


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
