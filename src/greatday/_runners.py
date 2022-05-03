"""Contains this project's clack runners."""

from __future__ import annotations

from collections import defaultdict
import datetime as dt
import json
from typing import Any, Dict, Final, Iterable, List

import clack
from clack.types import ClackRunner
from logrus import Logger
import magodo

from ._common import CTX_TODAY, drop_word_from_desc, is_tickler
from ._config import AddConfig, InfoConfig, ListConfig, TUIConfig
from ._repo import GreatRepo
from ._session import GreatSession
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
        and all(ctx not in todo.contexts for ctx in ["inbox", CTX_TODAY])
    ):
        contexts = list(todo.contexts) + ["inbox"]
        todo = todo.new(contexts=contexts)

    key = repo.add(todo).unwrap()
    log.info("Added new todo to inbox.", id=repr(key))
    print(todo.to_line())

    return 0


@runner
def run_info(cfg: InfoConfig) -> int:
    """Runner for the 'info' subcommand."""
    data: Dict[str, Any] = {}

    today = dt.date.today()
    repo_path = cfg.data_dir / TODO_DIR

    stats = data["stats"] = {}
    points_data = stats["points"] = {}
    day_info = points_data["by_day"] = defaultdict(dict)

    # e.g. 'stats.count.total' OR 'stats.count.open' OR 'stats.count.done'
    counter = stats["count"] = {}

    repo = GreatRepo(cfg.data_dir, repo_path)

    # 'stats.count' counter values
    done_count = 0
    open_count = 0
    tickler_count = 0

    for todo in repo.todo_group:
        if todo.done:
            done_count += 1
        else:
            open_count += 1

        # --- loop variables
        # key: used to index into the 'counter' dict.
        # tags: a dict of tags (e.g. projects) from the current todo.
        for key, props in [
            ("epic", todo.epics),
            ("project", todo.projects),
            ("context", todo.contexts),
        ]:
            for prop in props:
                if key not in counter:
                    counter[key] = defaultdict(int)

                counter[key][prop] += 1

        if "tickle" in list(todo.metadata.keys()):
            tickler_count += 1

    counter["done"] = done_count
    counter["open"] = open_count
    counter["tickler"] = tickler_count
    counter["total"] = open_count + done_count

    for days in range(cfg.points_start_offset, cfg.points_end_offset + 1):
        # inner (i.e. local to this for-loop) date
        date = today - dt.timedelta(days=days)

        day_total = 0
        xp_day_total = 0

        # Maps '@' contexts to numeric points.
        ctx_to_points: dict[str, int] = defaultdict(int)

        is_today = bool(date == today)

        with GreatSession(
            cfg.data_dir,
            repo_path,
            Tag(
                done_date=date,
                done=True,
                metadata_checks=[magodo.MetadataCheck("p")],
            ),
            name="info",
        ) as done_session:
            for todo in done_session.repo.todo_group:
                P = int(todo.metadata.get("p", 0))
                day_total += P
                xp_day_total += P
                for ctx in todo.contexts:
                    ctx_to_points[ctx] += P

        if is_today:
            # Add sum of 'xp' metatag values for todos due today...
            tag = Tag.from_query("@today xp !snooze done=0")
            with GreatSession(cfg.data_dir, repo_path, tag) as open_session:
                for todo in open_session.repo.todo_group:
                    XP = int(todo.metadata.get("xp", 0))
                    xp_day_total += XP

        if day_total or (xp_day_total and is_today):
            date_str = magodo.from_date(date)
            # Only show 'xp_total' for today's date...
            if is_today:
                day_info[date_str]["xp_total"] = xp_day_total

            day_info[date_str]["total"] = day_total
            day_info[date_str]["contexts"] = ctx_to_points

    pretty_data = json.dumps(data, indent=2, sort_keys=True)
    print(pretty_data)

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
