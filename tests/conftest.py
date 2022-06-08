"""This file contains shared fixtures and pytest hooks.

https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Iterator

from freezegun import freeze_time
from pytest import fixture

from greatday import db
from greatday.__main__ import main as gtd_main
from greatday._repo import SQLRepo
from greatday._todo import GreatTodo

from . import common as c


if TYPE_CHECKING:  # fixes pytest warning
    from clack.pytest_plugin import MakeConfigFile


pytest_plugins = ["clack.pytest_plugin"]


@fixture
def main(make_config_file: MakeConfigFile, tmp_path: Path) -> c.MainType:
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
    with freeze_time(f"{c.TODAY}T{c.hh}:{c.mm}:00.123456Z"):
        yield


@fixture
def sql_repo() -> Iterator[SQLRepo]:
    """SQLRepo pytext fixture

    Yields:
        A SQLRepo populated with dummy data.
    """
    url: Final = "sqlite://"
    key: Final = "DATABASE_URL"

    db.create_cached_engine.cache_clear()

    default_url = os.environ.setdefault(key, url)
    repo = SQLRepo(url)
    for line in c.TODO_LINES:
        todo = GreatTodo.from_line(line).unwrap()
        repo.add(todo).unwrap()

    yield repo

    if url == default_url:
        del os.environ[key]
