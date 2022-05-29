"""Common code used throughout this package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Final


if TYPE_CHECKING:
    from ._todo import GreatTodo


CTX_FIRST: Final = "FIRST"
CTX_INBOX: Final = "INBOX"
CTX_LAST: Final = "LAST"
CTX_TODAY: Final = "TODAY"


def drop_word_from_desc(
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


def is_tickler(todo: GreatTodo) -> bool:
    """Returns True iff `todo` is a tickler todo."""
    return bool(todo.metadata.get("tickle", None) is not None)
