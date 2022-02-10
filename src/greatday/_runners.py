"""Contains this project's clack runners."""

from __future__ import annotations

import datetime as dt
from functools import partial
from typing import Callable, Final, List

import clack
from clack.types import ClackRunner
from ion import getch
from logrus import Logger
import magodo
from typist import assert_never
from vimala import vim

from ._config import AddConfig, StartConfig
from ._repo import GreatRepo, Tag
from ._session import GreatSession
from ._todo import GreatTodo
from .types import YesNoDefault


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)

CTX_TODAY: Final = "today"
CTX_X: Final = "x"


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
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

    todo_dir = cfg.data_dir / "todos"

    process_inbox = bool(
        cfg.inbox == "y"
        or (cfg.inbox == "default" and last_start_date < today)
    )
    if process_inbox:
        logger.info(
            "Processing todos in your Inbox.",
            last_start_date=last_start_date,
        )
        with GreatSession(
            todo_dir, Tag(contexts=["inbox"], done=False), name="inbox"
        ) as session:
            edit_todos(session)
    else:
        logger.info(
            "Skipping Inbox processing (already processed today).",
            last_start_date=last_start_date,
        )

    process_ticklers = bool(
        cfg.ticklers == "y"
        or (cfg.ticklers == "default" and last_start_date < today)
    )
    if not process_ticklers:
        logger.info("Skipping tickler todos.")
    else:
        logger.info("Processing due tickler todos.")
        with GreatSession(
            todo_dir,
            Tag(metadata_checks={"tickle": tickle_check(today)}, done=False),
            name="ticklers",
        ) as session:
            edit_todos(session)

    logger.info("Processing todos selected for completion today.")
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


def drop_word_from_desc(
    desc: str,
    bad_word: str,
    *,
    key: Callable[[str, str], bool] = lambda x, y: x == y,
) -> str:
    """Removes `bad_word` from the todo description `desc`."""
    desc_words = desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if not key(word, bad_word):
            new_desc_words.append(word)
    return " ".join(new_desc_words)


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

    if (
        cfg.add_inbox_context
        and not x_found
        and all(ctx not in todo.contexts for ctx in ["inbox", CTX_TODAY])
    ):
        contexts = list(todo.contexts) + ["inbox"]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0
