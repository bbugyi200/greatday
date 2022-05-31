"""Contains the Tag class."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import operator
from typing import Any, Callable, Iterable

from logrus import Logger
import magodo
from magodo import DateRange, DescFilter, MetadataFilter
from magodo.types import Priority, SinglePredicate

from ._dates import (
    get_date_range,
    get_relative_date,
    matches_date_fmt,
    matches_relative_date_fmt,
)


logger = Logger(__name__)


@dataclass
class GreatTag:
    """A collection of `Tag`s that have been ORed together."""

    tags: list[Tag]

    @classmethod
    def from_query(cls, query: str) -> GreatTag:
        """Build a GreatTag using a query string."""
        tags: list[Tag] = []
        for subquery in query.split(" | "):
            tag = Tag.from_query(subquery)
            tags.append(tag)

        return cls(tags)


@dataclass(frozen=True)
class Tag:
    """Tag used to filter Todos."""

    contexts: Iterable[str] = ()
    create_date_ranges: Iterable[DateRange] = ()
    desc_filters: Iterable[DescFilter] = ()
    done_date_ranges: Iterable[DateRange] = ()
    done: bool | None = None
    epics: Iterable[str] = ()
    metadata_filters: Iterable[MetadataFilter] = ()
    priorities: Iterable[Priority] = ()
    projects: Iterable[str] = ()

    @classmethod
    def from_query(cls, query: str) -> Tag:  # noqa: C901
        """Build a Tag using a query string."""
        contexts: list[str] = []
        create_date_ranges: list[DateRange] = []
        desc_filters: list[DescFilter] = []
        done: bool | None = None
        done_date_ranges: list[DateRange] = []
        epics: list[str] = []
        metadata_filters: list[MetadataFilter] = []
        priorities: list[Priority] = []
        projects: list[str] = []

        for word in query.split(" "):
            # ----- Regular Tags (i.e. projects, epics, and contexts)
            is_a_tag = True
            for prefix, prop_list in [
                ("@", contexts),
                ("#", epics),
                ("+", projects),
            ]:
                if word.startswith(prefix):
                    logger.debug("Filter on property.", word=word)
                    prop_list.append(word[1:])
                    break

                if word.startswith(f"!{prefix}"):
                    logger.debug("Filter on negative property.", word=word)
                    prop_list.append(f"-{word[2:]}")
                    break
            else:
                is_a_tag = False

            if is_a_tag:
                continue

            # ----- Create and Done Dates
            is_a_date_range = False
            for ch, date_ranges in [
                ("^", create_date_ranges),
                ("$", done_date_ranges),
            ]:
                if word.startswith(ch):
                    date_range = get_date_range(word[1:])
                    date_ranges.append(date_range)
                    is_a_date_range = True

                    logger.debug(
                        "Filtering on date range.",
                        prefix=ch,
                        date_range=date_range,
                    )
                    break

            if is_a_date_range:
                continue

            # ----- Is open todo or done todo?
            if word.lower() == "x":
                done = True
                continue

            if word.lower() == "o":
                done = False
                continue

            # ----- Metatag Checks
            if word.isalpha():
                metadata_filters.append(MetadataFilter(word))
                continue

            if word.startswith("!") and word[1:].isalpha():
                metadata_filters.append(
                    MetadataFilter(
                        word[1:], check=lambda _: False, required=False
                    )
                )
                continue

            is_metatag_constraint = True
            for op_string, op in [
                ("<=", operator.le),
                (">=", operator.ge),
                ("<", operator.lt),
                (">", operator.gt),
                ("!=", operator.ne),
                ("=", operator.eq),
            ]:
                key_and_value_string = word.split(op_string)
                if len(key_and_value_string) != 2:
                    continue

                key, value_string = key_and_value_string

                required = not key.endswith("?")
                key = key.rstrip("?")

                value: dt.date | str | int
                if op_string in ["=", "!="]:
                    value = value_string
                elif matches_date_fmt(value_string):
                    value = magodo.to_date(value_string)
                elif matches_relative_date_fmt(value_string):
                    value = get_relative_date(value_string)
                elif value_string.isdigit():
                    value = int(value_string)
                else:
                    value = value_string

                check = _make_metadata_func(op, value)
                metadata_filters.append(
                    MetadataFilter(key, check=check, required=required)
                )
                break
            else:
                is_metatag_constraint = False

            if is_metatag_constraint:
                continue

        return cls(
            contexts=contexts,
            create_date_ranges=create_date_ranges,
            desc_filters=desc_filters,
            done_date_ranges=done_date_ranges,
            done=done,
            epics=epics,
            metadata_filters=metadata_filters,
            priorities=priorities,
            projects=projects,
        )


def _make_metadata_func(
    op: Callable[[Any, Any], bool], expected: Any
) -> SinglePredicate:
    def check(x: str) -> bool:
        actual: dt.date | str | int
        if isinstance(expected, dt.date):
            if matches_date_fmt(x):
                actual = magodo.to_date(x)
            else:
                return False
        elif isinstance(expected, int):
            if x.isdigit():
                actual = int(x)
            else:
                return False
        else:
            actual = x

        return op(actual, expected)

    return check
