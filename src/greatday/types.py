"""Custom types used by greatday."""

from __future__ import annotations

from dataclasses import dataclass
import enum
from typing import Any, Dict, Literal, Protocol, TypeVar

from magodo.types import AbstractTodo
from sqlalchemy.future import Engine
from typing_extensions import TypedDict


T = TypeVar("T", bound=AbstractTodo)


class SavedQueryGroup(TypedDict):
    """Represents a single saved query group."""

    default: str
    queries: Dict[str, str]


SavedQueryGroupMap = Dict[str, SavedQueryGroup]
YesNoDefault = Literal["n", "default", "y"]


class CreateEngineType(Protocol):
    """The type of a `db.create_engine()` callable."""

    def __call__(self, url: str, /, **kwargs: Any) -> Engine:
        """The function's call signature."""


class DescOperator(enum.Enum):
    """Used to determine the type of description constraint specified."""

    CONTAINS = enum.auto()
    NOT_CONTAINS = enum.auto()


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
class DescFilter:
    """Represents a description query filter (e.g. '"foo"' or '!"bar"')."""

    value: str
    case_sensitive: bool | None = None
    op: DescOperator = DescOperator.CONTAINS


@dataclass(frozen=True)
class MetatagFilter:
    """Represents a single metatag filter (e.g. 'due<=0d' or '!recur')."""

    key: str
    value: str = ""
    op: MetatagOperator = MetatagOperator.EXISTS
    value_type: MetatagValueType = MetatagValueType.STRING
