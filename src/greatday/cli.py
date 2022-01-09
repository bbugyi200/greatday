"""Contains the greatday package's main entry point."""

from __future__ import annotations

from typing import Sequence

import clack


class Config(clack.Config):
    """Command-line arguments."""

    @classmethod
    def from_cli_args(cls, argv: Sequence[str]) -> Config:
        """Parses command-line arguments."""
        parser = clack.Parser()

        args = parser.parse_args(argv[1:])
        kwargs = clack.filter_cli_args(args)

        return cls(**kwargs)


def run(cfg: Config) -> int:
    """This function acts as this tool's main entry point."""
    del cfg
    return 0


main = clack.main_factory("greatday", run)
