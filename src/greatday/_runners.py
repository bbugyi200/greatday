"""Contains this project's clack runners."""

from __future__ import annotations

import datetime as dt
from functools import partial
import json
from typing import Any, Callable, Dict, Final, List

import clack
from clack.types import ClackRunner
from ion import getch
from logrus import Logger
import magodo
from typist import assert_never
from vimala import vim

from ._common import CTX_TODAY, drop_word_from_desc, is_tickler
from ._config import AddConfig, InfoConfig, StartConfig
from ._repo import GreatRepo, Tag
from ._session import GreatSession
from ._todo import GreatTodo
from .types import YesNoDefault


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)

CTX_X: Final = "x"
TODO_DIR: Final = "todos"


@runner
def run_info(cfg: InfoConfig) -> int:
    """Runner for the 'info' subcommand."""
    data: Dict[str, Any] = {}

    today = dt.date.today()
    repo_path = cfg.data_dir / TODO_DIR

    day_info = data["points_by_day"] = {}
    for days in range(cfg.points_start_offset, cfg.points_end_offset + 1):
        ctx_to_points: dict[str, int] = {ctx: 0 for ctx in cfg.contexts}
        done_date = today - dt.timedelta(days=days)
        total = 0
        with GreatSession(
            repo_path,
            Tag(
                done_date=done_date,
                done=True,
                metadata_checks={"points": lambda _: True},
            ),
            name="info",
        ) as session:
            for todo in session.repo.todo_group:
                P = int(todo.metadata.get("points", "0"))
                total += P
                for ctx in cfg.contexts:
                    if ctx in todo.contexts:
                        ctx_to_points[ctx] += P

        date = magodo.from_date(done_date)
        day_info[date] = {"total": total}
        day_info[date]["contexts"] = ctx_to_points

    pretty_data = json.dumps(data, indent=2)
    print(pretty_data)

    return 0


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    log = logger.bind_fargs(locals())

    edit_todos = partial(
        edit_and_commit_todos, commit_changes=cfg.commit_changes
    )

    today = dt.date.today()
    last_start_date_file = cfg.data_dir / "last_start_date"
    if last_start_date_file.exists():
        assert last_start_date_file.is_file()
        last_start_string = last_start_date_file.read_text().strip()
    else:
        last_start_string = "1900-01-01"
    last_start_date = magodo.to_date(last_start_string)

    todo_dir = cfg.data_dir / TODO_DIR

    process_inbox = bool(
        cfg.inbox == "y"
        or (cfg.inbox == "default" and last_start_date < today)
    )
    if process_inbox:
        log.info(
            "Processing todos in your Inbox.",
            last_start_date=last_start_date,
        )
        with GreatSession(
            todo_dir, Tag(contexts=["inbox"], done=False), name="inbox"
        ) as session:
            edit_todos(session)
    else:
        log.info(
            "Skipping Inbox processing (already processed today).",
            last_start_date=last_start_date,
        )

    process_ticklers = bool(
        cfg.ticklers == "y"
        or (cfg.ticklers == "default" and last_start_date < today)
    )
    if process_ticklers:
        log.info("Processing due tickler todos.")
        with GreatSession(
            todo_dir,
            Tag(metadata_checks={"tickle": tickle_check(today)}, done=False),
            name="ticklers",
        ) as session:
            edit_todos(session)
    else:
        log.info("Skipping tickler todos.")

    process_daily = bool(cfg.daily in ["y", "default"])
    if process_daily:
        log.info("Processing todos selected for completion today.")
        name = "today." + magodo.from_date(today)
        with GreatSession(
            todo_dir,
            Tag(contexts=[CTX_TODAY]),
            name=name,
        ) as session:
            edit_todos(session)
            should_commit = False
            for todo in session.repo.todo_group:
                if CTX_X in todo.contexts:
                    contexts = tuple(
                        ctx
                        for ctx in todo.contexts
                        if ctx not in [CTX_X, CTX_TODAY]
                    )
                elif CTX_TODAY not in todo.contexts:
                    contexts = tuple(list(todo.contexts) + [CTX_TODAY])
                else:
                    continue

                should_commit = True
                new_todo = todo.new(contexts=contexts)
                session.repo.update(new_todo.ident, new_todo).unwrap()

            if should_commit:
                session.commit()
    else:
        log.info("Skipping daily todos.")

    if (
        all(
            opt in ["y", "default"]
            for opt in [cfg.daily, cfg.inbox, cfg.ticklers]
        )
        and last_start_date < today
    ):
        last_start_date_file.write_text(magodo.from_date(today))

    return 0


def edit_and_commit_todos(
    session: GreatSession,
    *,
    commit_changes: YesNoDefault = "default",
) -> None:
    """Edit and commit todo changes to disk."""
    old_todos = list(session.repo.todo_group)
    if not old_todos:
        return

    vim(session.path).unwrap()

    for otodo in old_todos:
        key = otodo.ident

        new_todo = session.repo.get(key).unwrap()
        if otodo != new_todo:
            break
    else:
        if len(old_todos) == len(session.repo.todo_group):
            return

    should_commit: bool
    if commit_changes == "y":
        should_commit = True
    elif commit_changes == "n":
        should_commit = False
    elif commit_changes == "default":
        should_commit = bool(
            getch("Commit these todo changes? (y/n): ") == "y"
        )
    else:
        assert_never(commit_changes)

    if should_commit:
        session.commit()
    else:
        session.rollback()


def tickle_check(today: dt.date) -> Callable[[str], bool]:
    """Returns MetadataChecker that returns all due ticklers."""

    def check(tickle_value: str) -> bool:
        due_date = magodo.to_date(tickle_value)
        return due_date <= today

    return check


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
    repo = GreatRepo(todo_dir)
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
        and all(ctx not in todo.contexts for ctx in ["inbox", CTX_TODAY])
    ):
        contexts = list(todo.contexts) + ["inbox"]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
