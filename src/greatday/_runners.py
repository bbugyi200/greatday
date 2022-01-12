"""Contains this project's clack runners.."""

from __future__ import annotations

from typing import List

import clack
from clack.types import ClackRunner

from ._config import StartConfig


ALL_RUNNERS: List[ClackRunner] = []
register_runner = clack.register_runner_factory(ALL_RUNNERS)


@register_runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the 'start' subcommand."""
    del cfg
    return 0
