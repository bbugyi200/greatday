"""Contains the greatday package's main entry point."""

from __future__ import annotations

import clack

from . import APP_NAME
from .config import clack_parser
from .runners import RUNNERS


main = clack.main_factory(APP_NAME, runners=RUNNERS, parser=clack_parser)
if __name__ == "__main__":
    main()
