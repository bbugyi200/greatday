"""Contains the Tag class."""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt
import operator
import string
from typing import Any, Callable, Iterable, cast

from eris import ErisResult, Err, Ok
from logrus import Logger
import magodo
from magodo import DateRange, DescFilter, MetadataFilter
from magodo.types import Priority, SinglePredicate

from ._dates import (
    RELATIVE_DATE_METATAGS,
    get_date_range,
    get_relative_date,
    matches_date_fmt,
    matches_relative_date_fmt,
)


logger = Logger(__name__)

GreatLangParser = Callable[[str], ErisResult[str]]


@dataclass(frozen=True)
class GreatTag:
    """A collection of `Tag`s that have been ORed together."""

    tags: Iterable[Tag]

    @classmethod
    def from_query(cls, query: str) -> GreatTag:
        """Build a GreatTag using a query string."""
        tags: list[Tag] = []
        for subquery in query.split(" | "):
            tag = Tag.from_query(subquery)
            tags.append(tag)

        return cls(tuple(tags))


@dataclass
class Tag:
    """Tag used to filter Todos."""

    contexts: list[str] = field(default_factory=list)
    create_date_ranges: list[DateRange] = field(default_factory=list)
    desc_filters: list[DescFilter] = field(default_factory=list)
    done_date_ranges: list[DateRange] = field(default_factory=list)
    done: bool | None = None
    epics: list[str] = field(default_factory=list)
    metadata_filters: list[MetadataFilter] = field(default_factory=list)
    priorities: list[Priority] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)

    @classmethod
    def from_query(cls, query: str) -> Tag:
        """Build a Tag using a query string."""
        tag = cls()

        q = query
        while q:
            for parser in [
                tag.prefix_tag_parser_factory("#", "epics"),
                tag.prefix_tag_parser_factory("@", "contexts"),
                tag.prefix_tag_parser_factory("+", "projects"),
                tag.done_parser,
                tag.date_range_parser_factory("^", "create_date_ranges"),
                tag.date_range_parser_factory("$", "done_date_ranges"),
                tag.metatag_parser,
                tag.desc_parser_factory("'"),
                tag.desc_parser_factory('"'),
                tag.priority_parser,
            ]:
                q_result = parser(q)
                if isinstance(q_result, Err):
                    err = q_result.err()
                    logger.debug(
                        "Parser failed to find match.",
                        parser=parser.__name__,
                        error=err.to_json(),
                    )
                else:
                    q = q_result.ok()
                    break
            else:
                raise RuntimeError(
                    "No parsers are able to parse this query. |"
                    f" query={query!r}"
                )

        return tag

    def prefix_tag_parser_factory(self, ch: str, attr: str) -> GreatLangParser:
        """Factory for parsers that handle normal tags (e.g. project tags)."""

        def parser(query: str) -> ErisResult[str]:
            prop_list = getattr(self, attr)
            word, *rest = query.split(" ")

            if word.startswith(ch):
                logger.debug("Filter on property.", word=word)
                prop_list.append(word[1:])
            elif word.startswith(f"!{ch}"):
                logger.debug("Filter on negative property.", word=word)
                prop_list.append(f"-{word[2:]}")
            else:
                return Err(
                    "First word of query does not match required tag prefix."
                    f" | prefix={ch} word={word}",
                )

            return Ok(" ".join(rest))

        return parser

    def done_parser(self, query: str) -> ErisResult[str]:
        """Parser for 'done' status (e.g. 'o' for open, 'x' for done)."""
        word, *rest = query.split(" ")
        if word.lower() == "o":
            self.done = False
        elif word.lower() == "x":
            self.done = True
        else:
            return Err("Next token is not 'o' or 'x'.")

        return Ok(" ".join(rest))

    def date_range_parser_factory(self, ch: str, attr: str) -> GreatLangParser:
        """Factory for create/done date range tokens."""

        def parser(query: str) -> ErisResult[str]:
            word, *rest = query.split(" ")
            if not word.startswith(ch):
                return Err("Next token is not a date range.")

            date_ranges = getattr(self, attr)
            date_range = get_date_range(word[1:])
            date_ranges.append(date_range)

            logger.debug(
                "Filtering on date range.",
                prefix=ch,
                date_range=date_range,
            )
            return Ok(" ".join(rest))

        return parser

    def metatag_parser(self, query: str) -> ErisResult[str]:
        """Parser for metadata checks."""
        word, *rest = query.split(" ")
        if word.isalpha():
            self.metadata_filters.append(MetadataFilter(word))
        elif word.startswith("!") and word[1:].isalpha():
            self.metadata_filters.append(
                MetadataFilter(word[1:], check=lambda _: False, required=False)
            )
        else:
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
                if (
                    op_string in ["=", "!="]
                    and key not in RELATIVE_DATE_METATAGS
                ):
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
                self.metadata_filters.append(
                    MetadataFilter(key, check=check, required=required)
                )
                break
            else:
                return Err("Next token is not a metadata check.")

        return Ok(" ".join(rest))

    def desc_parser_factory(self, quote: str) -> GreatLangParser:
        """Factory for parser that handles description tokens."""

        def parser(query: str) -> ErisResult[str]:
            filter_check = _contains
            q = query
            if q.startswith(f"!{quote}") or q.startswith(f"!c{quote}"):
                q = q[1:]
                filter_check = _does_not_contain

            case_sensitive = None
            if q.startswith(f"c{quote}"):
                q = q[1:]
                case_sensitive = True

            if q[0] != quote:
                return Err(
                    "Not a desc token (used to filter against a todo's"
                    " description)."
                )

            end_idx = q[1:].find(quote) + 1
            if end_idx == -1:
                return Err("Bad desc token. No ending quote found.")

            assert not q[end_idx + 1 :] or q[end_idx + 1] == " ", (
                "The character after the last quote should be a space."
                f" query={query}"
            )

            filter_value = q[1:end_idx]
            desc_filter = DescFilter(
                value=filter_value,
                check=filter_check,
                case_sensitive=case_sensitive,
            )
            self.desc_filters.append(desc_filter)
            return Ok(q[end_idx + 2 :])

        return parser

    def priority_parser(self, query: str) -> ErisResult[str]:
        """Parser for todo priority ranges."""
        word, *rest = query.split(" ")
        if word[0] != "(" or word[-1] != ")":
            return Err("Not a priority range.")

        for p in word[1:-1].split(","):
            priority: Priority
            if len(p) == 1:
                priority = cast(Priority, p.upper())
                assert (
                    priority in string.ascii_uppercase
                ), f"Bad priority value: {p}"
                self.priorities.append(priority)
            else:
                assert "-" in p, f"Bad priority range (no dash found): {p}"
                p_range = p.upper()
                start_p, end_p = p_range.split("-")
                n = ord(start_p)
                while n <= ord(end_p):
                    priority = cast(Priority, chr(n))
                    assert (
                        priority in string.ascii_uppercase
                    ), f"Bad priority value: {p}"
                    self.priorities.append(priority)
                    n += 1

        return Ok(" ".join(rest))


def _contains(small: str, big: str) -> bool:
    return small in big


def _does_not_contain(small: str, big: str) -> bool:
    return small not in big


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
