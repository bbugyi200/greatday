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
    op: Callable[[str, str], bool] = lambda x, y: x == y,
) -> str:
    """Removes `bad_word` from the todo description `desc`."""
    desc_words = desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if not op(word, bad_word):
            new_desc_words.append(word)
    return " ".join(new_desc_words)


def get_relative_date(spec: str, *, start_date: dt.date = None) -> dt.date:
    """Converts `spec` to a timedelta and adds it to `date`.

    Args:
        spec: A timedelta specification string (e.g. '1d', '2m', '3y',
          'weekdays').
        start_date: The return value is a function of this argument and the
          timedelta constructed from `spec`. Defaults to today's date.

    Examples:
        # Imports
        >>> import datetime as dt

        # Helper Functions
        >>> to_date = lambda x: dt.datetime.strptime(x, "%Y-%m-%d")
        >>> from_date = lambda x: x.strftime("%Y-%m-%d")
        >>> grd = lambda x, y: from_date(
        ...   get_relative_date(x, start_date=to_date(y))
        ... )

        # Default start date.
        >>> D = "2000-01-31"

        # Tests
        >>> grd("7d", D)
        '2000-02-07'

        >>> grd("7D", D)
        '2000-02-07'

        >>> grd("1m", D)
        '2000-02-29'

        >>> grd("1m", "2001-01-31")
        '2001-02-28'

        >>> grd("2M", D)
        '2000-03-31'

        >>> grd("3m", D)
        '2000-04-30'

        >>> grd("20y", D)
        '2020-01-31'

        >>> grd("weekdays", "2022-02-11")
        '2022-02-14'
    """
    spec = spec.lower()
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


def dt_from_date_and_hhmm(date: dt.date, hhmm: str) -> dt.datetime:
    """Given a date and a string of the form HHMM, construct a datetime."""
    spec = f"{date.year}-{date.month}-{date.day} {hhmm}"
    result = dt.datetime.strptime(spec, "%Y-%m-%d %H%M")
    return result


def matches_date_fmt(date_spec: str) -> bool:
    """Returns True iff date_spec matches the magodo date format.."""
    return len(date_spec) == 10 and date_spec.count("-") == 2
