"""This file contains shared fixtures and pytest hooks.

https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pytest import fixture

from greatday.__main__ import main as gtd_main


if TYPE_CHECKING:  # fixes pytest warning
    from clack.pytest_plugin import MakeConfigFile


pytest_plugins = ["clack.pytest_plugin"]


class MainType(Protocol):
    """Type returned by main() fixture."""

    def __call__(self, *args: str, **kwargs: Any) -> int:
        """The signature of the main() function."""


@fixture
def main(make_config_file: MakeConfigFile) -> MainType:
    """Returns a wrapper around greatday's main() function."""

    def inner_main(*args: str, **kwargs: Any) -> int:
        cfg_kwargs = {k: str(v) for (k, v) in kwargs.items()}
        config_file = make_config_file("greatday_test_config", **cfg_kwargs)
        argv = ["greatday", "-c", str(config_file.path)] + list(args)
        return gtd_main(argv)

    return inner_main
