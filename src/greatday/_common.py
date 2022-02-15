"""Common code used throughout this package."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Callable, Final

from dateutil.relativedelta import relativedelta


if TYPE_CHECKING:
    from ._todo import GreatTodo


CTX_TODAY: Final = "today"

MONDAY: Final = 0
TUESDAY: Final = 1
WEDNESDAY: Final = 2
THURSDAY: Final = 3
FRIDAY: Final = 4
SATURDAY: Final = 5
SUNDAY: Final = 6


def drop_word_from_desc(
    desc: str,
    bad_word: str,
    *,
    key: Callable[[str, str], bool] = lambda x, y: x == y,
) -> str:
    """Removes `bad_word` from the todo description `desc`."""
    desc_words = desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if not key(word, bad_word):
            new_desc_words.append(word)
    return " ".join(new_desc_words)


def get_relative_date(spec: str, *, start_date: dt.date = None) -> dt.date:
    """Converts `spec` to a timedelta and adds it to `date`.

    Args:
        spec: A timedelta specification string (e.g. '1d', '2m', '3y',
          'weekdays').
        date: The return value is a function of this argument and the
          timedelta constructed from `spec`. Defaults to today's date.

    Examples:
        # Imports
        >>> import datetime as dt

        # Helper Functions / Variables
        >>> to_date = lambda x: dt.datetime.strptime(x, "%Y-%m-%d")
        >>> from_date = lambda x: x.strftime("%Y-%m-%d")
        >>> start_date = to_date("2000-01-31")
        >>> grd = lambda x: from_date(
        ...   get_relative_date(x, start_date=start_date)
        ... )

        # Tests
        >>> grd("7d")
        '2000-02-07'

        >>> grd("1m")
        '2000-02-29'

        >>> grd("2m")
        '2000-03-31'

        >>> grd("3m")
        '2000-04-30'

        >>> grd("20y")
        '2020-01-31'
    """
    if start_date is None:
        start_date = dt.date.today()

    delta: dt.timedelta | relativedelta
    if spec == "weekdays":
        weekday = start_date.weekday()
        days = {FRIDAY: 3, SATURDAY: 2}.get(weekday, 1)
        delta = dt.timedelta(days=days)
    else:
        ch = spec[-1]
        N = int(spec[:-1])

        if ch == "d":
            delta = dt.timedelta(days=N)
        elif ch == "m":
            delta = relativedelta(months=N)
        else:
            assert ch == "y"
            delta = relativedelta(years=N)

    return start_date + delta


def is_tickler(todo: GreatTodo) -> bool:
    """Returns True iff `todo` is a tickler todo."""
    return bool(todo.metadata.get("tickle", None) is not None)
