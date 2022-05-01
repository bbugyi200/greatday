"""Contains the Tag class."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import operator
from typing import Any, Callable, Iterable

from logrus import Logger
import magodo
from magodo import MetadataCheck
from magodo.types import MetadataFunc, Priority

from ._common import matches_date_fmt


logger = Logger(__name__)


@dataclass(frozen=True)
class Tag:
    """Tag used to filter Todos."""

    contexts: Iterable[str] = ()
    create_date: dt.date | None = None
    done_date: dt.date | None = None
    done: bool | None = None
    epics: Iterable[str] = ()
    metadata_checks: Iterable[MetadataCheck] = ()
    priorities: Iterable[Priority] = ()
    projects: Iterable[str] = ()

    @classmethod
    def from_query(cls, query: str) -> Tag:
        """Build a Tag using a query string."""
        contexts: list[str] = []
        create_and_done: list[dt.date | None] = [None, None]
        done: bool | None = None
        epics: list[str] = []
        metadata_checks: list[MetadataCheck] = []
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
            is_date_range = False
            for i, date_prefix in enumerate(["create=", "done="]):
                if word.startswith(date_prefix):
                    date_spec = word[len(date_prefix) :]
                    if not matches_date_fmt(date_spec):
                        logger.debug(
                            "Date does not match required date format.",
                            date_spec=date_spec,
                        )
                        continue

                    create_and_done[i] = magodo.to_date(date_spec)
                    logger.debug(
                        "Filter on date.",
                        prefix=date_prefix,
                        date=create_and_done[i],
                    )
                    is_date_range = True

            if is_date_range:
                continue

            # ----- Is open todo or done todo?
            done_prefix = "done="
            if word.startswith(done_prefix):
                zero_or_one = word[len(done_prefix) :]
                if zero_or_one not in ["1", "0"]:
                    logger.warning(
                        "When using 'done=N', N must be either 0 or 1.",
                        N=zero_or_one,
                    )
                    continue

                done = bool(int(zero_or_one))
                logger.debug(
                    "Filter on whether todo is done or not.", done=done
                )
                continue

            # ----- Metatag Checks
            if word.isalpha():
                metadata_checks.append(MetadataCheck(word))

            if word.startswith("!") and word[1:].isalpha():
                metadata_checks.append(
                    MetadataCheck(
                        word[1:], check=lambda _: False, required=False
                    )
                )

            for op_string, op in [
                ("<=", operator.le),
                (">=", operator.ge),
                ("<", operator.lt),
                (">", operator.gt),
                (":", operator.eq),
            ]:
                key_and_value_string = word.split(op_string)
                if len(key_and_value_string) != 2:
                    continue

                key, value_string = key_and_value_string

                required = not key.endswith("?")
                key = key.rstrip("?")

                value: dt.date | str | float
                if op_string == ":":
                    value = value_string
                elif matches_date_fmt(value_string):
                    value = magodo.to_date(value_string)
                else:
                    value = float(value_string)

                check = _make_check(op, value)
                metadata_checks.append(
                    MetadataCheck(key, check=check, required=required)
                )
                break

        return cls(
            contexts=contexts,
            create_date=create_and_done[0],
            done_date=create_and_done[1],
            done=done,
            epics=epics,
            metadata_checks=metadata_checks,
            priorities=priorities,
            projects=projects,
        )


def _make_check(op: Callable[[Any, Any], bool], expected: Any) -> MetadataFunc:
    def check(actual: Any) -> bool:
        if isinstance(expected, dt.date):
            actual = magodo.to_date(actual)
        return op(actual, expected)

    return check
