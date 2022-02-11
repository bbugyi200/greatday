"""Common code used throughout this package."""

from typing import Callable, Final


CTX_TODAY: Final = "today"


def drop_word_from_desc(
    desc: str,
    bad_word: str,
    *,
    key: Callable[[str, str], bool] = lambda x, y: x == y,
) -> str:
    """Removes `bad_word` from the todo description `desc`."""
    desc_words = desc.split(" ")
    new_desc_words = []
    for word in desc_words:
        if not key(word, bad_word):
            new_desc_words.append(word)
    return " ".join(new_desc_words)
