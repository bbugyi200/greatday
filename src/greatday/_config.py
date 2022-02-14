"""Contains this project's clack.Config classes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Literal, Sequence

import clack
from clack import xdg

from . import APP_NAME
from .types import YesNoDefault


Command = Literal["add", "info", "list", "note", "start"]


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


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parser we pass to the `main_factory()` `parser` kwarg."""

    parser = clack.Parser(
        description="Don't have a good day. Have a great day."
    )

    new_command = clack.new_command_factory(parser)

    add_parser = new_command("add", help="Add a new todo to your inbox.")
    add_parser.add_argument(
        "todo_line",
        metavar="TODO",
        help=(
            "A valid todo string (i.e. a string that conforms to the standard"
            " todo.txt format)."
        ),
    )
    new_command(
        "start",
        help=(
            "Start the day by going through your inbox, ticklers, and finally"
            " a list of todos to have done before the end of the day."
        ),
    )
    new_command(
        "info",
        help=(
            "Print information about greatday and its current state to stdout"
            " in JSON format."
        ),
    )

    args = parser.parse_args(argv[1:])
    kwargs = clack.filter_cli_args(args)

    return kwargs
