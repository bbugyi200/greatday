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
        create_date: dt.date | None = None
        done_date: dt.date | None = None
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
                if word.startswith("^"):
                    date_spec = word[1:]
                    if not matches_date_fmt(date_spec):
                        logger.warning(
                            "Create date does not match required date format.",
                            date_spec=date_spec,
                        )
                        continue

                    create_date = magodo.to_date(date_spec)
                    logger.debug(
                        "Filter on create date.", create_date=create_date
                    )
                    continue

                if word.startswith("$"):
                    date_spec = word[1:]
                    if not matches_date_fmt(date_spec):
                        logger.warning(
                            "Done date does not match required date format.",
                            date_spec=date_spec,
                        )
                        continue

                    done_date = magodo.to_date(date_spec)
                    logger.debug("Filter on done date.", done_date=done_date)
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
            create_date=create_date,
            done_date=done_date,
            done=done,
            epics=epics,
            metadata_checks=metadata_checks,
            priorities=priorities,
            projects=projects,
        )
