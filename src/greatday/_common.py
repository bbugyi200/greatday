"""Common code used throughout this package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Final


if TYPE_CHECKING:
    from ._todo import GreatTodo


CTX_INBOX: Final = "INBOX"
CTX_TODAY: Final = "TODAY"


def drop_word_from_desc(
    desc: str,
    bad_word: str,
    *,
    op: Callable[[str, str], bool] = lambda x, y: x == y,
) -> str:
    """Removes `bad_word` from the todo description `desc`."""
    desc_words = desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if not op(word, bad_word):
            new_desc_words.append(word)
    return " ".join(new_desc_words)


def is_tickler(todo: GreatTodo) -> bool:
    """Returns True iff `todo` is a tickler todo."""
    return bool(todo.metadata.get("tickle", None) is not None)
