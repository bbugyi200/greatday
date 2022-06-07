"""This file contains shared fixtures and pytest hooks.

https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Protocol

from freezegun import freeze_time
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
def main(make_config_file: MakeConfigFile, tmp_path: Path) -> MainType:
    """Returns a wrapper around greatday's main() function."""

    data_dir = tmp_path / "data"
    database_url = "sqlite://"

    def inner_main(*args: str, **kwargs: Any) -> int:
        if "data_dir" not in kwargs:
            kwargs["data_dir"] = data_dir

        if "database_url" not in kwargs:
            kwargs["database_url"] = database_url

        cfg_kwargs = {k: str(v) for (k, v) in kwargs.items()}

        config_file = make_config_file("greatday_test_config", **cfg_kwargs)
        argv = ["greatday", "-c", str(config_file.path)] + list(args)
        return gtd_main(argv)

    return inner_main


@fixture(autouse=True, scope="session")
def frozen_time() -> Iterator[None]:
    """Freeze time until our tests are done running."""
    with freeze_time("2000-01-01T00:00:00.123456Z"):
        yield
