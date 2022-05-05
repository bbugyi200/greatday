"""Editor (e.g. vim) code lives here."""

from __future__ import annotations

from vimala import vim

from ._session import GreatSession


def edit_and_commit_todos(session: GreatSession) -> None:
    """Edit and commit todo changes to disk."""
    old_todos = list(session.repo.todo_group)
    if not old_todos:
        return

    vim(session.path).unwrap()

    for old_todo in old_todos:
        key = old_todo.ident

        new_todo = session.repo.get(key).unwrap()
        if old_todo != new_todo:
            break
    else:
        if len(old_todos) == len(session.repo.todo_group):
            return

    session.commit()
