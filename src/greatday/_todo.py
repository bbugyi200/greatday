"""Contains greatday's custom Todo types."""

from __future__ import annotations

from typing import Any, cast

import magodo
from magodo import MagicTodoMixin
from magodo.types import Priority
from sqlmodel import Session, select

from . import _spells as spells, db, models
from ._common import drop_word_if_startswith
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
    def from_model(cls, mtodo: models.Todo) -> GreatTodo:
        """Construct a GreatTodo from a Todo model class."""
        contexts = tuple(ctx.name for ctx in mtodo.contexts)
        epics = tuple(epic.name for epic in mtodo.epics)
        projects = tuple(project.name for project in mtodo.projects)

        metadata = {"id": str(mtodo.id)}
        for mlink in mtodo.metatag_links:
            key = mlink.metatag.name
            value = mlink.value
            metadata[key] = value

        priority = cast(Priority, mtodo.priority)
        magodo_todo = magodo.Todo(
            contexts=contexts,
            create_date=mtodo.create_date,
            desc=mtodo.desc,
            done=mtodo.done,
            done_date=mtodo.done_date,
            epics=epics,
            priority=priority,
            projects=projects,
            metadata=metadata,
        )
        return cls(magodo_todo)

    def to_model(self, session: Session, key: str = None) -> models.Todo:
        """Converts a GreatTodo into something that the DB can work with."""
        mtodo_kwargs: dict[str, Any] = dict(
            create_date=self.create_date,
            desc=drop_word_if_startswith(self.desc, "id:"),
            done=self.done,
            done_date=self.done_date,
            priority=self.priority,
        )

        metadata = dict(self.metadata.items())
        id_metatag = metadata.get("id")
        if id_metatag:
            # we don't want to duplicate this in our DB (the primary key will
            # have the same value)
            del metadata["id"]

        if key is not None:
            mtodo_kwargs["id"] = int(key)

        if id_metatag is None:
            mtodo = models.Todo(**mtodo_kwargs)

        stmt: Any
        for attr, tag_model in [
            ("contexts", models.Context),
            ("epics", models.Epic),
            ("projects", models.Project),
        ]:
            tag_list = getattr(self, attr)
            model_tag_list = getattr(mtodo, attr)
            for name in tag_list:
                stmt = select(tag_model).where(tag_model.name == name)
                results = session.exec(stmt)
                tag = results.first()
                if tag is None:
                    tag = tag_model(name=name)

                model_tag_list.append(tag)

        for k, v in metadata.items():
            stmt = select(models.Metatag).where(models.Metatag.name == k)
            results = session.exec(stmt)
            metatag = results.first()
            if metatag is None:
                metatag = models.Metatag(name=k)

            mlink = models.MetatagLink(metatag=metatag, todo=mtodo, value=v)
            mtodo.metatag_links.append(mlink)

        return mtodo


def main() -> None:
    """Test driver for this module."""
    import sys

    engine = db.cached_engine("sqlite:///greatday.db")
    with Session(engine) as sess:
        todo = GreatTodo.from_line(
            f"o {sys.argv[1]} | @home +pig due:2022-06-02"
        ).unwrap()
        mtodo = todo.to_model(sess)
        sess.add(mtodo)
        sess.commit()


if __name__ == "__main__":
    main()
