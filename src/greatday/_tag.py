"""Contains the Tag class."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from typing import Iterable

from logrus import Logger
import magodo
from magodo import MetadataCheck
from magodo.types import Priority

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
