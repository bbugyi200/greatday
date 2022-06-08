"""Contains the Tag class."""

from __future__ import annotations

from dataclasses import dataclass, field
import enum
import string
from typing import Callable, Iterable, cast

from eris import ErisResult, Err, Ok
from logrus import Logger
import magodo
from magodo.types import Priority

from ._dates import (
    RELATIVE_DATE_METATAGS,
    DateRange,
    get_date_range,
    get_relative_date,
    matches_date_fmt,
    matches_relative_date_fmt,
)


logger = Logger(__name__)

QueryParser = Callable[[str], ErisResult[str]]


class MetatagOperator(enum.Enum):
    """Used to determine what kind of metatag constraint has been specified."""

    # exists / not exists
    EXISTS = enum.auto()
    NOT_EXISTS = enum.auto()

    # comparison operators
    EQ = enum.auto()
    NE = enum.auto()
    LT = enum.auto()
    LE = enum.auto()
    GT = enum.auto()
    GE = enum.auto()


class MetatagValueType(enum.Enum):
    """Specifies the data type of a MetatagFilter's value."""

    DATE = enum.auto()
    INTEGER = enum.auto()
    STRING = enum.auto()


@dataclass(frozen=True)
class MetatagFilter:
    """Represents a single metatag filter (e.g. 'due<=0d' or '!recur')."""

    key: str
    value: str = ""
    op: MetatagOperator = MetatagOperator.EXISTS
    value_type: MetatagValueType = MetatagValueType.STRING


class DescOperator(enum.Enum):
    """Used to determine the type of description constraint specified."""

    CONTAINS = enum.auto()
    NOT_CONTAINS = enum.auto()


@dataclass(frozen=True)
class DescFilter:
    """Represents a description query filter (e.g. '"foo"' or '!"bar"')."""

    value: str
    case_sensitive: bool | None = None
    op: DescOperator = DescOperator.CONTAINS


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
    metatag_filters: list[MetatagFilter] = field(default_factory=list)
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

    def prefix_tag_parser_factory(self, ch: str, attr: str) -> QueryParser:
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

    def date_range_parser_factory(self, ch: str, attr: str) -> QueryParser:
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
            self.metatag_filters.append(
                MetatagFilter(word, op=MetatagOperator.EXISTS)
            )
        elif word.startswith("!") and word[1:].isalpha():
            self.metatag_filters.append(
                MetatagFilter(word[1:], op=MetatagOperator.NOT_EXISTS)
            )
        else:
            for op_string, metatag_op in [
                ("<=", MetatagOperator.LE),
                (">=", MetatagOperator.GE),
                ("<", MetatagOperator.LT),
                (">", MetatagOperator.GT),
                ("!=", MetatagOperator.NE),
                ("=", MetatagOperator.EQ),
            ]:
                key_and_value_string = word.split(op_string)
                if len(key_and_value_string) != 2:
                    continue

                key, value_string = key_and_value_string

                value = value_string
                value_type = MetatagValueType.STRING
                if (
                    op_string in ["=", "!="]
                    and key not in RELATIVE_DATE_METATAGS
                ):
                    pass
                elif matches_date_fmt(value_string):
                    value_type = MetatagValueType.DATE
                elif matches_relative_date_fmt(value_string):
                    value = magodo.dates.from_date(
                        get_relative_date(value_string)
                    )
                    value_type = MetatagValueType.DATE
                elif value_string.isdigit():
                    value_type = MetatagValueType.INTEGER

                self.metatag_filters.append(
                    MetatagFilter(
                        key,
                        value=value,
                        op=metatag_op,
                        value_type=value_type,
                    )
                )
                break
            else:
                return Err("Next token is not a metadata check.")

        return Ok(" ".join(rest))

    def desc_parser_factory(self, quote: str) -> QueryParser:
        """Factory for parser that handles description tokens."""

        def parser(query: str) -> ErisResult[str]:
            desc_op = DescOperator.CONTAINS
            q = query
            if q.startswith(f"!{quote}") or q.startswith(f"!c{quote}"):
                q = q[1:]
                desc_op = DescOperator.NOT_CONTAINS

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
                op=desc_op,
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
