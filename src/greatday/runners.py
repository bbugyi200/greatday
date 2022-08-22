"""Contains this project's clack runners."""

from __future__ import annotations

from functools import partial
from typing import Final, List

from clack.types import ClackRunner
from logrus import Logger
import metaman
from vimala import vim

from . import tui
from .common import CTX_INBOX, drop_words
from .config import AddConfig, ListConfig, TUIConfig
from .repo import SQLRepo
from .session import GreatSession
from .tag import GreatTag
from .todo import GreatTodo


RUNNERS: List[ClackRunner] = []
runner = metaman.register_function_factory(RUNNERS)

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
    repo = SQLRepo(cfg.database_url)

    # get default active query
    query = tui.get_default_query(
        cfg.saved_query_groups, cfg.default_query_group
    )

    ctx = tui.Context(query, cfg.default_query_group)
    run_app = partial(
        tui.GreatApp.run,
        repo=repo,
        ctx=ctx,
        saved_query_group_map=cfg.saved_query_groups,
        title="Greatday TUI",
        log="greatday_textual.log",
    )
    run_app()

    while ctx.edit_todos:
        tag = GreatTag.from_query(ctx.query)
        with GreatSession(
            cfg.database_url, tag, verbose=cfg.verbose
        ) as session:
            vim(session.path).unwrap()
            session.commit()

        ctx.edit_todos = False
        run_app()

    return 0
