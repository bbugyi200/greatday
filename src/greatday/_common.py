"""Common code used throughout this package."""

from __future__ import annotations

from typing import Callable, Final


CTX_FIRST: Final = "FIRST"
CTX_INBOX: Final = "INBOX"
CTX_LAST: Final = "LAST"


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
