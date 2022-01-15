"""Contains the greatday package's main entry point."""

from __future__ import annotations

import clack

from . import APP_NAME
from ._config import clack_parser
from ._runners import ALL_RUNNERS


main = clack.main_factory(APP_NAME, runners=ALL_RUNNERS, parser=clack_parser)
if __name__ == "__main__":
    main()
