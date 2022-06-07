"""Test utils used by multiple modules."""

from __future__ import annotations

from typing import Any, Protocol


# dummy todo lines.. used as test data
TODO_LINES = (
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

# the database IDs that should be associated with each of the todo lines above
TODO_LINE_IDS = tuple(str(n) for n in range(1, len(TODO_LINES) + 1))

# Parameters used by test_get_by_tag() test function.
#
# query -> ids
#
# query: used to construct GreatTag objects
# ids: iist of todo line IDs that this query should match
QUERY_TO_TODO_IDS: list[tuple[str, list[int]]] = [
    ("", [1, 2, 3, 4, 5]),
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


class MainType(Protocol):
    """Type returned by main() fixture."""

    def __call__(self, *args: str, **kwargs: Any) -> int:
        """The signature of the main() function."""
