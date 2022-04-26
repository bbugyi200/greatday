"""Contains this project's clack.Config classes."""

from __future__ import annotations

import itertools as it
from pathlib import Path
from typing import Any, List, Literal, Optional, Sequence

import clack
from clack import xdg

from . import APP_NAME
from .types import YesNoDefault


Command = Literal["add", "info", "list", "note", "start", "tui"]


class Config(clack.Config):
    """Command-line arguments."""

    command: Command

    # ----- CONFIG
    contexts: List[str] = ["dev", "me", "work"]
    data_dir: Path = xdg.get_full_dir("data", APP_NAME)


class StartConfig(Config):
    """Config for the 'start' subcommand."""

    command: Literal["start"]

    # ----- CONFIG
    commit_changes: YesNoDefault = "default"
    daily: YesNoDefault = "default"
    ticklers: YesNoDefault = "default"
    inbox: YesNoDefault = "default"


class AddConfig(Config):
    """Config for the 'add' subcommand."""

    command: Literal["add"]

    # ----- ARGUMENTS
    todo_line: str

    # ----- CONFIG
    add_inbox_context: YesNoDefault = "default"


class InfoConfig(Config):
    """Config for the 'info' subcommand."""

    command: Literal["info"]

    # ----- CONFIG
    points_start_offset: int = 0
    points_end_offset: int = 4


class ListConfig(Config):
    """Config for the 'list' subcommand."""

    command: Literal["list"]

    # ----- ARGUMENTS
    query: Optional[str] = None


class TUIConfig(Config):
    """Config for the 'tui' subcommand."""

    command: Literal["tui"]


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parser we pass to the `main_factory()` `parser` kwarg."""
    # HACK: Make 'tui' the default sub-command.
    if not list(it.dropwhile(lambda x: x.startswith("-"), argv[1:])):
        argv = list(argv) + ["tui"]

    parser = clack.Parser(
        description="Don't have a good day. Have a great day."
    )

    new_command = clack.new_command_factory(parser)

    # ----- 'tui' command (default)
    new_command(
        "tui",
        help=(
            "Render greatday's text-based user interface (TUI). This is the"
            " default command."
        ),
    )

    # ----- 'add' command
    add_parser = new_command("add", help="Add a new todo to your inbox.")
    add_parser.add_argument(
        "todo_line",
        metavar="TODO",
        help=(
            "A valid todo string (i.e. a string that conforms to the standard"
            " todo.txt format)."
        ),
    )

    # ----- 'start' command
    new_command(
        "start",
        help=(
            "Start the day by going through your inbox, ticklers, and finally"
            " a list of todos to have done before the end of the day."
        ),
    )

    # ----- 'info' command
    new_command(
        "info",
        help=(
            "Print information about greatday and its current state to stdout"
            " in JSON format."
        ),
    )

    # ----- 'list' command
    list_parser = new_command("list", help="Query the todo database.")
    list_parser.add_argument(
        "query",
        nargs="?",
        help=(
            "The todo search query that will be used to filter todos. If not"
            " provided, all todos are selected."
        ),
    )

    args = parser.parse_args(argv[1:])
    kwargs = clack.filter_cli_args(args)

    return kwargs
