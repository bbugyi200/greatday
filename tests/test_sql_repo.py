"""Tests for greatday's SQLRepo class."""

from __future__ import annotations

from pytest import fixture, mark

from greatday import db
from greatday._repo import SQLRepo
from greatday._tag import GreatTag
from greatday._todo import GreatTodo


params = mark.parametrize

# dummy todo lines.. used as test data
_TODO_LINES = (
    # ID #1
    "o 2000-01-01 Do some Laundry | @home @boring foo:bar",
    # ID #2
    "(B) 2000-02-03 Buy groceries | @out @boring +buy foo:bar due:2000-02-03",
    # ID #3
    "x 2010-01-02 2010-01-01 Finish greatday tests | @dev +greatday"
    " mile:2 p:0",
    # ID #4
    "o 1900-01-01 Finish greatday tests | @dev +greatday due:2000-01-01",
    # ID #5
    "x 2022-06-05 Some other todo | @misc p:1",
)
TODO_LINES = tuple(line + " ctime:HHMM" for line in _TODO_LINES)

# the database IDs that should be associated with each of the todo lines above
TODO_LINE_IDS = tuple(str(n) for n in range(1, len(TODO_LINES) + 1))

# Parameters used by test_get_by_tag() test function.
#
# query -> ids
#
# query: used to construct GreatTag objects
# ids: iist of todo line IDs that this query should match
QUERY_TO_TODO_IDS: list[tuple[str, list[int]]] = [
    ("o", [1, 2, 4]),
    ("x", [3, 5]),
    ("@home", [1]),
    ("!@home", [2, 3, 4, 5]),
    ("!@home @boring", [2]),
    ("@home @boring", [1]),
    ("@boring", [1, 2]),
    ("+greatday", [3, 4]),
    ("+buy @boring", [2]),
    ("(a)", []),
    ("(b)", [2]),
    ("(a-b)", [2]),
    ("(a,b)", [2]),
    ("due", [2, 4]),
    ("!due", [1, 3, 5]),
    ("due=2000-01-01", [4]),
    ("due>=2000-01-01", [2, 4]),
    ("due>2000-01-01", [2]),
    ("p", [3, 5]),
    ("p>0", [5]),
    ("^2000-01-01", [1]),
    ("^2000-01-01:2010-12-31", [1, 2, 3]),
    ("^2000-01-01:2010-12-31 $2010-01-01", []),
    ("^2000-01-01:2010-12-31 $2010-01-02", [3]),
    ('"some"', [1, 5]),
    ('!"some"', [2, 3, 4]),
    ('"Some"', [5]),
    ('!"Some"', [1, 2, 3, 4]),
    ('c"some"', [1]),
    ('!c"some"', [2, 3, 4, 5]),
    ("id=2", [2]),
    ("id>2", [3, 4, 5]),
]


@fixture(name="repo")
def sql_repo_fixture() -> SQLRepo:
    """Returns a SQLRepo populated with dummy data."""
    repo = SQLRepo("sqlite://", engine_factory=db.create_engine)
    for line in TODO_LINES:
        todo = GreatTodo.from_line(line).unwrap()
        repo.add(todo).unwrap()
    return repo


def test_add(repo: SQLRepo) -> None:
    """Tests the SQLRepo.add() method.

    NOTE: Nothing needs to be done here since the repo fixture invokes the
    SQLRepo.add() method for us.
    """
    assert len(TODO_LINES) == len(repo.all().unwrap())


@params("key", TODO_LINE_IDS)
def test_get_and_remove(repo: SQLRepo, key: str) -> None:
    """Tests the SQLRepo.get() and SQLRepo.remove() methods."""
    todo = repo.get(key).unwrap()
    assert todo == repo.remove(key).unwrap()
    assert len(TODO_LINES) == len(repo.all().unwrap()) + 1


@params("key", TODO_LINE_IDS)
def test_update(repo: SQLRepo, key: str) -> None:
    """Tests the SQLRepo.update() method."""
    old_todo = GreatTodo.from_line(
        TODO_LINES[int(key) - 1] + f" id:{key}"
    ).unwrap()
    todo = GreatTodo.from_line(
        f"o foobar @foo @bar ctime:HHMM id:{key}"
    ).unwrap()

    actual_old_todo = repo.update(key, todo).unwrap()
    assert old_todo == actual_old_todo

    actual_todo = repo.get(key).unwrap()
    assert todo == actual_todo


@params("query,keys", QUERY_TO_TODO_IDS)
def test_get_by_tag(repo: SQLRepo, query: str, keys: list[str]) -> None:
    """Tests the SQLRepo.get_by_tag() method."""
    tag = GreatTag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()
    assert sorted(todo.ident for todo in todos) == sorted(str(k) for k in keys)


def test_remove_by_tag(repo: SQLRepo) -> None:
    """Tests the SQLRepo.remove_by_tag() method."""
    CTX = "@dev"
    matched_line_count = len(
        [line for line in TODO_LINES if CTX in line.split(" ")]
    )
    tag = GreatTag.from_query(CTX)
    removed_todos = repo.remove_by_tag(tag).unwrap()
    assert len(removed_todos) == matched_line_count
    assert len(repo.all().unwrap()) == len(TODO_LINES) - matched_line_count
