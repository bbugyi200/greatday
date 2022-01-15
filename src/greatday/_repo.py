"""Contains helper utilities for working with greatday's "database".

We place "database" in quotes since greatday explicitly shuns traditional
databases, choosing to store all todos in text format.

NOTE: This module implements the "Repository" abstraction.
"""

from clack import xdg
from potoroo import Repository


class GreatRepo(Repository):
    """Repo that stores Todos on disk."""
