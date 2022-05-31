"""Contains this project's clack runners."""

from __future__ import annotations

from typing import Final, Iterable, List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._common import CTX_INBOX, drop_word_from_desc
from ._config import AddConfig, ListConfig, TUIConfig
from ._repo import GreatRepo
from ._tag import GreatTag
from ._todo import GreatTodo
from ._tui import start_textual_app


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)

CTX_X: Final = "x"


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    repo = GreatRepo(cfg.data_dir)
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
        and CTX_INBOX not in todo.contexts
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
    repo = GreatRepo(cfg.data_dir)

    todo_iter: Iterable[GreatTodo]
    if cfg.query is None:
        todo_iter = repo.todo_group
    else:
        tag = GreatTag.from_query(cfg.query)
        todo_iter = repo.get_by_tag(tag).unwrap()

    for todo in sorted(todo_iter):
        print(todo.to_line())

    return 0


@runner
def run_tui(cfg: TUIConfig) -> int:
    """Runer for the 'tui' subcommand."""
    start_textual_app(cfg.data_dir)
    return 0
