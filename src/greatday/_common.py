"""Common code used throughout this package."""

from __future__ import annotations

from functools import lru_cache as cache, partial
from typing import Callable, Final, List, cast

from magodo.types import Priority
from typist import literal_to_list


# special contexts
CTX_FIRST: Final = "FIRST"
CTX_INBOX: Final = "INBOX"
CTX_LAST: Final = "LAST"

# special ID type (assigned when no real ID exists)
NULL_ID: Final = "null"

# all valid todo lines must start with one of...
TODO_PREFIXES: Final = ("x ", "x:", "o ")


def drop_words(
    desc: str,
    *bad_words: str,
    op: Callable[[str, str], bool] = lambda x, y: x == y,
) -> str:
    """Removes all `bad_words` from the todo description `desc`."""
    desc_words = desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if not any(op(word, bad_word) for bad_word in bad_words):
            new_desc_words.append(word)
    return " ".join(new_desc_words)


def _startswith_op(x: str, y: str) -> bool:
    """Used as the value for the 'op' kwarg of `drop_word_from_desc()`."""
    return x.startswith(y)


drop_word_if_startswith = partial(drop_words, op=_startswith_op)


@cache
def todo_prefixes() -> tuple[str, ...]:
    """Returns all valid todo prefixes."""
    result = list(TODO_PREFIXES)
    for P in cast(List[str], literal_to_list(Priority)):
        result.append(f"({P}) ")
    return tuple(result)
