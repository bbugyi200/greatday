"""Common code used throughout this package."""

import datetime as dt
from typing import Callable, Final


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


def get_tdelta(spec: str, *, today: dt.date = None) -> dt.timedelta:
    """Converts a string spec to a timedelta."""
    if today is None:
        today = dt.date.today()

    if spec == "weekday":
        weekday = today.weekday()
        days = {FRIDAY: 3, SATURDAY: 2}.get(weekday, 1)
    else:
        assert spec[-1] == "d"
        days = int(spec[:-1])

    return dt.timedelta(days=days)
