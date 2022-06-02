"""Contains greatday's custom Todo types."""

from __future__ import annotations

from typing import Any, cast

import magodo
from magodo import MagicTodoMixin
from magodo.types import Priority
from sqlmodel import Session, select

from . import _spells as spells, db, models
from ._ids import NULL_ID


class GreatTodo(MagicTodoMixin):
    """Custom MagicTodo type used when working with Todos in the daily file."""

    pre_todo_spells = spells.GREAT_PRE_TODO_SPELLS
    todo_spells = spells.GREAT_TODO_SPELLS
    post_todo_spells = spells.GREAT_POST_TODO_SPELLS

    to_line_spells = spells.GREAT_TO_LINE_SPELLS
    from_line_spells = spells.GREAT_FROM_LINE_SPELLS

    @property
    def ident(self) -> str:
        """Returns this Todo's unique identifier."""
        result = self.metadata.get("id", NULL_ID)
        return result

    @classmethod
    def from_model(cls, todo: models.Todo) -> GreatTodo:
        """Construct a GreatTodo from a Todo model class."""
        contexts = tuple(ctx.name for ctx in todo.contexts)
        epics = tuple(epic.name for epic in todo.epics)
        projects = tuple(project.name for project in todo.projects)

        metadata = {}
        for mlink in todo.metatag_links:
            key = mlink.metatag.name
            value = mlink.value
            metadata[key] = value

        priority = cast(Priority, todo.priority)
        magodo_todo = magodo.Todo(
            contexts=contexts,
            create_date=todo.create_date,
            desc=todo.desc,
            done=todo.done,
            done_date=todo.done_date,
            epics=epics,
            priority=priority,
            projects=projects,
            metadata=metadata,
        )
        return cls(magodo_todo)

    def to_model(self, session: Session) -> models.Todo:
        """Converts a GreatTodo into something that the DB can work with."""
        todo_kwargs: dict[str, Any] = dict(
            create_date=self.create_date,
            desc=self.desc,
            done=self.done,
            done_date=self.done_date,
            priority=self.priority,
        )

        if self.ident != NULL_ID:
            todo_kwargs["id"] = int(self.ident)

        for attr, tag_model in [
            ("contexts", models.Context),
            ("epics", models.Epic),
            ("projects", models.Project),
        ]:
            tag_list = getattr(self, attr)
            model_tag_list = []
            for name in tag_list:
                stmt = select(tag_model).where(tag_model.name == name)
                results = session.exec(stmt)
                tag = results.first()
                if tag is None:
                    tag = tag_model(name=name)

                model_tag_list.append(tag)

            todo_kwargs[attr] = model_tag_list

        todo = models.Todo(**todo_kwargs)

        return todo


if __name__ == "__main__":
    import sys

    engine = db.cached_engine("sqlite:///greatday.db")
    with Session(engine) as sess:
        gtodo = GreatTodo.from_line(f"o {sys.argv[1]} | +pig @home").unwrap()
        mtodo = gtodo.to_model(sess)
        sess.add(mtodo)
        sess.commit()
