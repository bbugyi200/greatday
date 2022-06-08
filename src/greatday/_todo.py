"""Contains greatday's custom Todo types."""

from __future__ import annotations

from typing import Any, cast

from eris import ErisResult, Err, Ok
import magodo
from magodo import MagicTodoMixin
from magodo.types import Priority
from sqlmodel import Session, select

from . import _spells as spells, models
from ._common import NULL_ID, drop_word_if_startswith


_LINE_TO_TODO_CACHE: dict[str, "GreatTodo"] = {}


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
    def from_line(cls, line: str) -> ErisResult[GreatTodo]:
        """Override's default implementation in order to add caching."""
        todo = _LINE_TO_TODO_CACHE.get(line)
        if todo is None:
            result = super().from_line(line)
            if isinstance(result, Err):
                return result

            todo = result.ok()
            _LINE_TO_TODO_CACHE[line] = todo

        return Ok(todo)

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
        todo = magodo.Todo(
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
        return cls(todo)

    def to_model(self, session: Session, key: str = None) -> models.Todo:
        """Converts a GreatTodo into something that the DB can work with."""
        metadata = dict(self.metadata.items())
        id_metatag = metadata.get("id")
        if id_metatag is not None:
            # we don't want to duplicate this in our DB (the primary key will
            # have the same value)
            del metadata["id"]

        if key is None and id_metatag is not None:
            key = id_metatag

        desc = drop_word_if_startswith(self.desc, "id:")
        mtodo_kwargs: dict[str, Any] = dict(
            create_date=self.create_date,
            desc=desc,
            done=self.done,
            done_date=self.done_date,
            priority=self.priority,
        )

        stmt: Any
        if key is None:
            mtodo = models.Todo(**mtodo_kwargs)
        else:
            stmt = select(models.Todo).where(models.Todo.id == int(key))
            results = session.exec(stmt)
            maybe_mtodo = results.first()
            if maybe_mtodo is None:
                mtodo = models.Todo(**mtodo_kwargs)
                mtodo.id = int(key)
            else:
                mtodo = maybe_mtodo
                for k, v in mtodo_kwargs.items():
                    setattr(mtodo, k, v)

        for attr, tag_model in [
            ("contexts", models.Context),
            ("epics", models.Epic),
            ("projects", models.Project),
        ]:
            self_tag_list = getattr(self, attr)
            model_tag_list = []
            for tag_name in self_tag_list:
                stmt = select(tag_model).where(tag_model.name == tag_name)
                results = session.exec(stmt)
                tag = results.first()
                if tag is None:
                    tag = tag_model(name=tag_name)

                model_tag_list.append(tag)
            setattr(mtodo, attr, model_tag_list)

        metatag_links = []
        for k, v in metadata.items():
            stmt = select(models.Metatag).where(models.Metatag.name == k)
            results = session.exec(stmt)
            metatag = results.first()
            if metatag is None:
                metatag = models.Metatag(name=k)

            stmt = (
                select(models.MetatagLink)
                .where(models.MetatagLink.todo_id == mtodo.id)
                .where(models.MetatagLink.metatag_id == metatag.id)
            )
            results = session.exec(stmt)
            mlink = results.first()

            if mlink is None:
                mlink = models.MetatagLink(
                    metatag=metatag, todo=mtodo, value=v
                )

            metatag_links.append(mlink)

        mtodo.metatag_links = metatag_links
        return mtodo
