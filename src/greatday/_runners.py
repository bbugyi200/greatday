"""Contains this project's clack runners."""

from __future__ import annotations

from typing import Final, List

from clack.types import ClackRunner
from logrus import Logger
import metaman

from ._common import CTX_INBOX, drop_words
from ._config import AddConfig, ListConfig, TUIConfig
from ._repo import SQLRepo
from ._tag import GreatTag
from ._todo import GreatTodo
from ._tui import start_textual_app


ALL_RUNNERS: List[ClackRunner] = []
runner = metaman.register_function_factory(ALL_RUNNERS)

logger = Logger(__name__)

CTX_X: Final = "x"


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the 'add' subcommand."""
    log = logger.bind_fargs(locals())

    repo = SQLRepo(cfg.database_url, verbose=cfg.verbose)
    todo = GreatTodo.from_line(cfg.todo_line).unwrap()

    x_found = False
    if CTX_X in todo.contexts:
        x_found = True
        desc = drop_words(todo.desc, f"@{CTX_X}")
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
    repo = SQLRepo(cfg.database_url, verbose=cfg.verbose)

    query: str
    if cfg.query is None:
        query = ""
    else:
        query = cfg.query

    tag = GreatTag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()

    for todo in sorted(todos):
        print(todo.to_line())

    return 0


@runner
def run_tui(cfg: TUIConfig) -> int:
    """Runer for the 'tui' subcommand."""
    start_textual_app(cfg.database_url, verbose=cfg.verbose)
    return 0
