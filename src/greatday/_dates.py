"""Greatday date utilities."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Final

from dateutil.relativedelta import relativedelta
from typist import PathLike


MONDAY: Final = 0
TUESDAY: Final = 1
WEDNESDAY: Final = 2
THURSDAY: Final = 3
FRIDAY: Final = 4
SATURDAY: Final = 5
SUNDAY: Final = 6


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


def dt_from_date_and_hhmm(date: dt.date, hhmm: str) -> dt.datetime:
    """Given a date and a string of the form HHMM, construct a datetime."""
    spec = f"{date.year}-{date.month}-{date.day} {hhmm}"
    result = dt.datetime.strptime(spec, "%Y-%m-%d %H%M")
    return result


def matches_date_fmt(date_spec: str) -> bool:
    """Returns True iff date_spec matches the magodo date format.."""
    return len(date_spec) == 10 and date_spec.count("-") == 2


def matches_relative_date_fmt(date_spec: str) -> bool:
    """Returns True iff date_spec appears to be a relative date (e.g. 1d)."""
    return (
        len(date_spec) > 1
        and date_spec[:-1].isdigit()
        and date_spec[-1].lower() in ["d", "m", "y"]
    )


def init_yyyymm_path(root: PathLike, *, date: dt.date = None) -> Path:
    """Returns a Path of the form /path/to/root/YYYY/MM.txt.

    NOTE: Creates the /path/to/root/YYYY directory if necessary.
    """
    root = Path(root)
    if date is None:
        date = dt.date.today()

    year = date.year
    month = date.month

    result = root / str(year) / f"{month:0>2}.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    return result