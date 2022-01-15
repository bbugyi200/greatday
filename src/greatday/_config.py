"""Contains this project's clack.Config classes.."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

import clack
from clack import xdg

from . import APP_NAME


Command = Literal["add", "info", "list", "note", "start"]


class Config(clack.Config):
    """Command-line arguments."""

    command: Command

    # ----- CONFIG
    data_dir: Path = xdg.get_full_dir("data", APP_NAME)


class StartConfig(Config):
    """Config for the 'start' subcommand."""

    command: Literal["start"]


class AddConfig(Config):
    """Config for the 'add' subcommand."""

    command: Literal["add"]

    todo_line: str


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parser we pass to the `main_factory()` `parser` kwarg."""

    parser = clack.Parser(
        description="Don't have a good day. Have a great day."
    )

    new_command = clack.new_command_factory(parser)

    new_command("start", help="")

    add_parser = new_command("add", help="Add a new todo to your inbox.")
    add_parser.add_argument(
        "todo_line",
        metavar="TODO",
        help=(
            "A valid todo string (i.e. a string that conforms to the standard"
            " todo.txt format)."
        ),
    )

    args = parser.parse_args(argv[1:])
    kwargs = clack.filter_cli_args(args)

    return kwargs
