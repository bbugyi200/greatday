"""Greatday date utilities."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from typing import Final, Protocol

from dateutil.relativedelta import relativedelta
import magodo


# metatags (i.e. key-value tags) that accept relative date strings (e.g. '1d')
RELATIVE_DATE_METATAGS: Final = ["snooze", "until", "due"]

_DEFAULT_YEAR: Final[int] = -1
_FRIDAY: Final[int] = 4
_SATURDAY: Final[int] = 5


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


class MondayMaker(Protocol):
    """Signature for a function that returns Mondays."""

    def __call__(self, *, year: int = _DEFAULT_YEAR) -> list[dt.date]:
        """The function's call signature."""


def get_mondays(*, year: int = _DEFAULT_YEAR) -> list[dt.date]:
    """Returns all mondays of a given year.

    Examples:
        >>> mondays = get_mondays(year=2020)
        >>> len(mondays)
        52

        >>> mondays[0]
        datetime.date(2020, 1, 6)

        >>> mondays[-1]
        datetime.date(2020, 12, 28)

        >>> mondays = get_mondays(year=2021)
        >>> len(mondays)
        52

        >>> mondays[0]
        datetime.date(2021, 1, 4)

        >>> mondays[-1]
        datetime.date(2021, 12, 27)
    """
    if year == _DEFAULT_YEAR:
        year = dt.date.today().year

    d = dt.date(year, 1, 1)
    while d.weekday() != 0:
        d += dt.timedelta(days=1)

    mondays = []
    while d.year == year:
        mondays.append(d)
        d += dt.timedelta(weeks=1)
    return mondays


def get_quarter_mondays(*, year: int = _DEFAULT_YEAR) -> list[dt.date]:
    """Returns every first Monday of every quarter from `year`.

    Examples:
        >>> quarter_mondays = get_quarter_mondays(year=2020)
        >>> len(quarter_mondays)
        4
        >>> quarter_mondays[0]
        datetime.date(2020, 1, 6)
        >>> quarter_mondays[1]
        datetime.date(2020, 4, 6)
        >>> quarter_mondays[2]
        datetime.date(2020, 7, 6)
        >>> quarter_mondays[3]
        datetime.date(2020, 10, 5)

        >>> quarter_mondays = get_quarter_mondays(year=2021)
        >>> len(quarter_mondays)
        4
        >>> quarter_mondays[0]
        datetime.date(2021, 1, 4)
        >>> quarter_mondays[1]
        datetime.date(2021, 4, 5)
        >>> quarter_mondays[2]
        datetime.date(2021, 7, 5)
        >>> quarter_mondays[3]
        datetime.date(2021, 10, 4)
    """
    mondays = []
    for i, monday in enumerate(get_mondays(year=year)):
        if i % 13 == 0:
            mondays.append(monday)
    return mondays


def get_month_mondays(*, year: int = _DEFAULT_YEAR) -> list[dt.date]:
    """Returns a list of Mondays that begin a month.

    By month here, we are referring to a "greatday month", which is either the
    first day of the quarter, 4 weeks from that day, or 8 weeks from that day.

    Examples:
        >>> month_mondays = get_month_mondays(year=2020)
        >>> len(month_mondays)
        12

        >>> month_mondays[0]
        datetime.date(2020, 1, 6)

        >>> month_mondays[1]
        datetime.date(2020, 2, 3)

        >>> month_mondays[2]
        datetime.date(2020, 3, 2)

        >>> month_mondays[3]
        datetime.date(2020, 4, 6)

        >>> month_mondays[4]
        datetime.date(2020, 5, 4)

        >>> month_mondays[5]
        datetime.date(2020, 6, 1)

        >>> month_mondays[6]
        datetime.date(2020, 7, 6)

        >>> month_mondays[7]
        datetime.date(2020, 8, 3)

        >>> month_mondays[8]
        datetime.date(2020, 8, 31)

        >>> month_mondays[9]
        datetime.date(2020, 10, 5)

        >>> month_mondays[10]
        datetime.date(2020, 11, 2)

        >>> month_mondays[11]
        datetime.date(2020, 11, 30)

        >>> month_mondays = get_month_mondays(year=2021)
        >>> len(month_mondays)
        12

        >>> month_mondays[0]
        datetime.date(2021, 1, 4)

        >>> month_mondays[1]
        datetime.date(2021, 2, 1)

        >>> month_mondays[2]
        datetime.date(2021, 3, 1)

        >>> month_mondays[3]
        datetime.date(2021, 4, 5)

        >>> month_mondays[4]
        datetime.date(2021, 5, 3)

        >>> month_mondays[5]
        datetime.date(2021, 5, 31)

        >>> month_mondays[6]
        datetime.date(2021, 7, 5)

        >>> month_mondays[7]
        datetime.date(2021, 8, 2)

        >>> month_mondays[8]
        datetime.date(2021, 8, 30)

        >>> month_mondays[9]
        datetime.date(2021, 10, 4)

        >>> month_mondays[10]
        datetime.date(2021, 11, 1)

        >>> month_mondays[11]
        datetime.date(2021, 11, 29)
    """
    month_indices = [0, 4, 8, 13, 17, 21, 26, 30, 34, 39, 43, 47]
    mondays = []
    for i, monday in enumerate(get_mondays(year=year)):
        if any(i == n for n in month_indices):
            mondays.append(monday)
    return mondays


def get_next_monday(
    date: dt.date | None = None, *, monday_maker: MondayMaker = get_mondays
) -> dt.date:
    """Returns next Monday relative to `date`.

    Examples:
        >>> get_next_monday(dt.date(2020, 1, 1))
        datetime.date(2020, 1, 6)

        >>> get_next_monday(dt.date(2020, 1, 2))
        datetime.date(2020, 1, 6)

        >>> get_next_monday(dt.date(2020, 1, 3))
        datetime.date(2020, 1, 6)

        >>> get_next_monday(dt.date(2020, 1, 4))
        datetime.date(2020, 1, 6)

        >>> get_next_monday(dt.date(2020, 1, 5))
        datetime.date(2020, 1, 6)

        >>> get_next_monday(dt.date(2020, 1, 6))
        datetime.date(2020, 1, 13)

        >>> get_next_monday(
        ...     dt.date(2020, 1, 1),
        ...     monday_maker=get_quarter_mondays)
        datetime.date(2020, 1, 6)

        >>> get_next_monday(
        ...     dt.date(2020, 2, 1),
        ...     monday_maker=get_quarter_mondays)
        datetime.date(2020, 4, 6)

        >>> get_next_monday(
        ...     dt.date(2020, 3, 1),
        ...     monday_maker=get_quarter_mondays)
        datetime.date(2020, 4, 6)

        >>> get_next_monday(
        ...     dt.date(2020, 4, 1),
        ...     monday_maker=get_quarter_mondays)
        datetime.date(2020, 4, 6)

        >>> get_next_monday(
        ...     dt.date(2020, 5, 1),
        ...     monday_maker=get_quarter_mondays)
        datetime.date(2020, 7, 6)

        >>> get_next_monday(
        ...     dt.date(2020, 6, 1),
        ...     monday_maker=get_quarter_mondays)
        datetime.date(2020, 7, 6)
    """
    if date is None:
        date = dt.date.today()

    for d in monday_maker(year=date.year):
        if d > date:
            return d

    raise RuntimeError("No next Monday found! This should not be possible!")


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
        days = {_FRIDAY: 3, _SATURDAY: 2}.get(weekday, 1)
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
