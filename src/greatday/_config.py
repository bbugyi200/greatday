"""Contains this project's clack.Config classes.."""

from __future__ import annotations

from typing import Any, Literal, Sequence

import clack


Command = Literal["start", "note", "add", "list"]


class Config(clack.Config):
    """Command-line arguments."""

    command: Command


class StartConfig(Config):
    """Config for the 'start' subcommand."""

    command: Literal["start"]


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parser we pass to the `main_factory()` `parser` kwarg."""

    parser = clack.Parser(
        description="Don't have a good day. Have a great day."
    )

    new_command = clack.new_command_factory(parser)

    new_command("start", help="")

    args = parser.parse_args(argv[1:])
    kwargs = clack.filter_cli_args(args)

    return kwargs
