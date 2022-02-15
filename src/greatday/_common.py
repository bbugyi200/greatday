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
        spec: A timedelta specification string (e.g. '1d', 'monthly',
          'weekdays').
        date: The return value is a function of this argument and the
          timedelta constructed from `spec`. Defaults to today's date.

    Examples:
        # Imports
        >>> import datetime as dt
        >>> from functools import partial

        # Helper Functions
        >>> to_date = lambda x: dt.datetime.strptime(x, "%Y-%m-%d")
        >>> from_date = lambda x: x.strftime("%Y-%m-%d")

        >>> start_date = to_date("2000-01-01")

        >>> next_date = get_relative_date("7d", start_date=start_date)
        >>> from_date(next_date)
        '2000-01-08'

        >>> next_date = get_relative_date("monthly", start_date=start_date)
        >>> from_date(next_date)
        '2000-02-01'
    """
    if start_date is None:
        start_date = dt.date.today()

    if spec == "monthly":
        return start_date + relativedelta(months=1)
    elif spec == "weekdays":
        weekday = start_date.weekday()
        days = {FRIDAY: 3, SATURDAY: 2}.get(weekday, 1)
    else:
        assert spec[-1] == "d"
        days = int(spec[:-1])

    return start_date + dt.timedelta(days=days)


def is_tickler(todo: GreatTodo) -> bool:
    """Returns True iff `todo` is a tickler todo."""
    return bool(todo.metadata.get("tickle", None) is not None)
