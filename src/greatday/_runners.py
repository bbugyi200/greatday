"""Contains this project's clack runners."""

from __future__ import annotations

from typing import Final, Iterable, List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._common import CTX_INBOX, CTX_TODAY, drop_word_from_desc, is_tickler
from ._config import AddConfig, ListConfig, TUIConfig
from ._repo import GreatRepo
from ._tag import Tag
from ._todo import GreatTodo
from ._tui import start_textual_app


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)

CTX_X: Final = "x"
TODO_DIR: Final = "todos"


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    todo_dir = cfg.data_dir / "todos"
    repo = GreatRepo(cfg.data_dir, todo_dir)
    todo = GreatTodo.from_line(cfg.todo_line).unwrap()

    x_found = False
    if CTX_X in todo.contexts:
        x_found = True
        desc = drop_word_from_desc(todo.desc, f"@{CTX_X}")
        contexts = [ctx for ctx in todo.contexts if ctx != CTX_X]
        todo = todo.new(desc=desc, contexts=contexts)

    if cfg.add_inbox_context == "y" or (
        cfg.add_inbox_context == "default"
        and not x_found
        and not is_tickler(todo)
        and all(ctx not in todo.contexts for ctx in [CTX_INBOX, CTX_TODAY])
    ):
        contexts = list(todo.contexts) + [CTX_INBOX]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0


@runner
def run_list(cfg: ListConfig) -> int:
    """Runner for the 'list' subcommand."""
    repo_path = cfg.data_dir / TODO_DIR
    repo = GreatRepo(cfg.data_dir, repo_path)

    todo_iter: Iterable[GreatTodo]
    if cfg.query is None:
        todo_iter = repo.todo_group
    else:
        tag = Tag.from_query(cfg.query)
        todo_iter = repo.get_by_tag(tag).unwrap()

    for todo in sorted(todo_iter):
        print(todo.to_line())

    return 0


@runner
def run_tui(cfg: TUIConfig) -> int:
    """Runer for the 'tui' subcommand."""
    repo_path = cfg.data_dir / TODO_DIR
    start_textual_app(cfg.data_dir, repo_path)
    return 0
