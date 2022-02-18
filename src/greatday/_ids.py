"""ID generating logic lives here."""

from __future__ import annotations

from pathlib import Path
from typing import Container, Final

from typist import PathLike


NULL_ID: Final = "null"


def init_next_todo_id(data_dir: PathLike) -> str:
    """Retrieves the next valid todo ID.

    Side Effects:
        * Attempts to read last ID from disk.
        * Writes the returned ID to disk.
    """
    data_dir = Path(data_dir)
    last_id_path = data_dir / "last_todo_id"
    last_id_path.parent.mkdir(parents=True, exist_ok=True)

    def ID(next_id: str) -> str:
        with last_id_path.open("w+"):
            last_id_path.write_text(next_id)
        return next_id

    if last_id_path.exists():
        last_id = last_id_path.read_text().strip()
        next_id = next_todo_id(last_id)
        return ID(next_id)
    else:
        return ID("0")


def next_todo_id(last_id: str) -> str:
    """Determines the next ID from the last ID.

    Examples:
        >>> next_todo_id('0')
        '1'

        >>> next_todo_id('9')
        'A'

        >>> next_todo_id('Z')
        '00'

        >>> next_todo_id('ZZ')
        '000'

        >>> next_todo_id('AZ')
        'B0'

        >>> next_todo_id('BM9')
        'BMA'

        >>> next_todo_id('BMZ')
        'BN0'

        >>> next_todo_id('BZZ')
        'C00'

        >>> next_todo_id('0ZZ')
        '100'

        >>> next_todo_id('C00')
        'C01'

        # we skip 'I', since it can be confused with '1'...
        >>> next_todo_id('BZH')
        'BZJ'

        # we skip 'O', since it can be confused with '0'...
        >>> next_todo_id('BZN')
        'BZP'

        >>> next_todo_id('B9Z')
        'BA0'
    """
    for i, ch in enumerate(reversed(last_id)):
        if ch != "Z":
            idx = len(last_id) - (i + 1)
            zeros = "0" * i
            return last_id[:idx] + next_char(last_id[idx]) + zeros

    zeros = "0" * (len(last_id) + 1)
    return zeros


def next_char(ch: str, *, blacklist: Container[str] = ("I", "O")) -> str:
    """Returns the next allowable character (to be used as apart of ID)."""
    if ch == "9":
        return "A"

    result = chr(ord(ch) + 1)
    while result in blacklist:
        result = chr(ord(result) + 1)
    return result
