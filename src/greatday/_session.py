"""Contains the GreatSession class."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import string
import tempfile
from types import TracebackType
from typing import Type, cast

from logrus import Logger
import magodo
from magodo.types import Priority
from potoroo import Repo, UnitOfWork

from ._common import NULL_ID
from ._dates import get_relative_date
from ._repo import FileRepo, SQLRepo
from ._tag import GreatTag
from ._todo import GreatTodo


logger = Logger(__name__)


class GreatSession(UnitOfWork[FileRepo]):
    """Each time todos are opened in an editor, a new session is created."""

    def __init__(
        self,
        db_url: str,
        tag: GreatTag = None,
        *,
        name: str = None,
        verbose: int = 0,
    ) -> None:
        self.db_url = db_url

        prefix = None if name is None else f"{name}."
        _, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".txt")
        self.path = Path(temp_path)

        self._master_repo = SQLRepo(self.db_url, verbose=verbose)
        self._key_to_old_todo = {}
        if tag is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a+") as f:
                for todo in sorted(self._master_repo.get_by_tag(tag).unwrap()):
                    f.write(todo.to_line() + "\n")
                    self._key_to_old_todo[todo.ident] = todo

        # will be accessed via `self.repo` from this point forward
        self._repo = FileRepo(self.path)

    def __enter__(self) -> GreatSession:
        """Called before entering a GreatSession with-block."""
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Called before exiting a GreatSession with-block."""
        del exc_type
        del exc_value
        del traceback

        os.unlink(self.path)

    def commit(self) -> None:
        """Commit our changes.

        We achieve this by copying the contents of the backup file created on
        instantiation back to the original.
        """
        removed_todo_keys = list(self._key_to_old_todo.keys())
        new_todos = {}
        for todo in self.repo.all().unwrap():
            key = todo.ident
            if key in removed_todo_keys:
                removed_todo_keys.remove(key)

            old_todo = self._key_to_old_todo.get(key)
            if key == NULL_ID:
                logger.info("New todo was added while editing?", todo=todo)
                key = self._master_repo.add(todo).unwrap()
                new_todos[key] = todo
            elif todo != old_todo:
                _commit_todo_changes(self._master_repo, todo, old_todo)

        if new_todos:
            # HACK: Removes all new todos by assuming that new todos will not
            # have been assigned an ID yet.
            old_lines = self.path.read_text().split("\n")
            self.path.write_text(
                "\n".join(line for line in old_lines if " id:" in line)
            )

        for key, todo in new_todos.items():
            self._key_to_old_todo[key] = todo
            self.repo.add(todo, key=key)

        for key in removed_todo_keys:
            removed_todo = self._master_repo.remove(key).unwrap()
            if removed_todo is not None:
                logger.info("Todo has been deleted.", todo=removed_todo)
                del self._key_to_old_todo[removed_todo.ident]

    def rollback(self) -> None:
        """Revert any changes made while in this GreatSession's with-block."""

    @property
    def repo(self) -> FileRepo:
        """Returns the GreatRepo object associated with this GreatSession."""
        return self._repo


def _commit_todo_changes(
    repo: Repo[str, GreatTodo], todo: GreatTodo, old_todo: GreatTodo | None
) -> None:
    """Updates todo in repo.

    This function also handles recurring todos (i.e. todos with the
    'recur' metatag).
    """
    recur = todo.metadata.get("recur")
    until = todo.metadata.get("until")
    expired = bool(
        todo.done_date
        and until
        and magodo.dates.to_date(until) <= todo.done_date
    )
    if (
        old_todo
        and todo.done_date
        and not old_todo.done_date
        and recur
        and not expired
    ):
        next_metadata = dict(todo.metadata.items())

        # set 'prev' and 'xp' metatags for next todo...
        next_metadata["prev"] = next_metadata["id"]
        del next_metadata["id"]
        if next_metadata.get("p"):
            del next_metadata["p"]

        # set 'due' metatag for next todo...
        due = todo.metadata.get("due")
        if recur.islower() or due is None:
            start_date = todo.done_date
        else:
            start_date = magodo.dates.to_date(due)

        next_date = get_relative_date(recur, start_date=start_date)
        next_metadata["due"] = magodo.dates.from_date(next_date)

        # set creation date + clear creation/done time for next todo...
        next_create_date = dt.date.today()
        for key in ["ctime", "dtime"]:
            if key in next_metadata:
                del next_metadata[key]

        # set priority for next todo...
        priority = todo.metadata.get("priority")
        next_priority = magodo.DEFAULT_PRIORITY
        if (
            priority
            and len(priority) == 1
            and priority.upper() in string.ascii_uppercase
        ):
            next_priority = cast(Priority, priority.upper())
        elif priority:
            logger.warning("Bad 'priority' metatag value?", priority=priority)

        # add next todo to repo...
        next_todo = todo.new(
            create_date=next_create_date,
            done=False,
            done_date=None,
            metadata=next_metadata,
            priority=next_priority,
        )
        next_key = repo.add(next_todo).unwrap()

        # add 'next' metatag to old todo...
        metadata = dict(todo.metadata.items())
        metadata["next"] = next_key
        todo = todo.new(metadata=metadata)

    repo.update(todo.ident, todo).unwrap()
