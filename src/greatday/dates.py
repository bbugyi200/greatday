"""Greatday date utilities."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from typing import Final

from dateutil.relativedelta import relativedelta
import magodo


MONDAY: Final = 0
TUESDAY: Final = 1
WEDNESDAY: Final = 2
THURSDAY: Final = 3
FRIDAY: Final = 4
SATURDAY: Final = 5
SUNDAY: Final = 6

# metatags (i.e. key-value tags) that accept relative date strings (e.g. '1d')
RELATIVE_DATE_METATAGS: Final = ["snooze", "until", "due"]


@dataclass(frozen=True)
class DateRange:
    """Represents a range of dates."""

    start: dt.date
    end: dt.date | None = None

    @classmethod
    def from_strings(cls, start_str: str, end_str: str = None) -> DateRange:
        """Constructs a DateRange from two strings."""
        start = magodo.dates.to_date(start_str)
        end = magodo.dates.to_date(end_str) if end_str else None
        return cls(start, end)


def get_relative_date(
    spec: str, *, start_date: dt.date = None, past: bool = False
) -> dt.date:
    """Converts `spec` to a timedelta and adds it to `date`.

    Args:
        spec: A timedelta specification string (e.g. '1d', '2m', '3y',
          'weekdays').
        start_date: The return value is a function of this argument and the
          timedelta constructed from `spec`. Defaults to today's date.
        past: If set, we use a relative date from the past instead of the
          future (e.g. '1d' will yield yesterday's date instead of today's).

    Examples:
        # Imports
        >>> import datetime as dt

        # Helper Functions
        >>> to_date = lambda x: dt.datetime.strptime(x, "%Y-%m-%d")
        >>> from_date = lambda x: x.strftime("%Y-%m-%d")
        >>> grd = lambda x, y: from_date(
        ...   get_relative_date(x, start_date=to_date(y))
        ... )
        >>> past_grd = lambda x, y: from_date(
        ...   get_relative_date(x, start_date=to_date(y), past=True)
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

        >>> past_grd("1d", D)
        '2000-01-30'
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

    if past:
        return start_date - delta
    else:
        return start_date + delta


def dt_from_date_and_hhmm(date: dt.date, hhmm: str) -> dt.datetime:
    """Given a date and a string of the form HHMM, construct a datetime."""
    spec = f"{date.year}-{date.month}-{date.day} {hhmm}"
    result = dt.datetime.strptime(spec, "%Y-%m-%d %H%M")
    return result


def matches_date_fmt(spec: str) -> bool:
    """Returns True iff spec matches the magodo date format.."""
    return len(spec) == 10 and spec.count("-") == 2


def matches_relative_date_fmt(spec: str) -> bool:
    """Returns True iff spec appears to be a relative date (e.g. 1d)."""
    return (
        len(spec) > 1
        and spec[:-1].isdigit()
        and spec[-1].lower() in ["d", "m", "y"]
    )


def to_great_date(spec: str, past: bool = False) -> dt.date:
    """Converts a date string into a date.

    Args:
        spec: The date string specification (use a supported date format).
        past: Treat relative dates (e.g. when `spec == "1d"`) as dates in
          the past instead of the future.

    NOTE: `spec` must match a date string specification supported by
    greatday (e.g. 'YYYY-MM-DD').
    """
    if matches_date_fmt(spec):
        return magodo.dates.to_date(spec)
    else:
        assert matches_relative_date_fmt(spec)
        return get_relative_date(spec, past=past)


def get_date_range(spec: str) -> DateRange:
    """Constructs a date range from a `spec`.

    Args:
        spec: date specification which MUST use a format of START:END where
          START and END are valid date specs (e.g. `2000-01-01`; '1d'; '5m:0d').

    Examples:
        # setup
        >>> a = "2000-01-01"
        >>> b = "2000-01-31"

        # tests
        >>> a_range = get_date_range(a)
        >>> a_range.start
        datetime.date(2000, 1, 1)
        >>> a_range.end is None
        True

        >>> ab_range = get_date_range(f"{a}:{b}")
        >>> ab_range.start
        datetime.date(2000, 1, 1)
        >>> ab_range.end
        datetime.date(2000, 1, 31)
    """
    start_and_end = [to_great_date(x, past=True) for x in spec.split(":")]
    if len(start_and_end) > 1:
        assert len(start_and_end) == 2
        start, end = start_and_end
    else:
        start = start_and_end[0]
        end = None

    return DateRange(start, end)
