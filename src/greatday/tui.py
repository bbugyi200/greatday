"""Functions / classes used to create greatday's TUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Sequence

from potoroo import TaggedRepo
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, Static

from .tag import GreatTag
from .todo import GreatTodo
from .types import SavedQueryGroup, SavedQueryGroupMap


# HACK: Used to fix action parameter parenthesis bug (see PR:textual#562).
_FAKE_RIGHT_PAREN: Final = "]]]"

# default saved query group
_DEFAULT_QUERY_GROUP: SavedQueryGroup = {
    "queries": {"all": ""},
    "default": "all",
}

# number of seconds in-between full TUI refreshes
_REFRESH_INTERVAL: Final = 60


class GreatHeader(Header):
    """Override the default Header for Styling"""

    def __init__(self) -> None:
        super().__init__(show_clock=True)
        self.tall = False
        self.style = Style(color="white", bgcolor="rgb(98,98,98)")


class GreatFooter(Footer):
    """Override the default Footer for Styling"""


class StatsWidget(Static, can_focus=True):
    """Widget that shows Todo statistics."""

    def __init__(
        self,
        repo: TaggedRepo[str, GreatTodo, GreatTag],
        ctx: Context,
        saved_query_group_map: SavedQueryGroupMap,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__("", *args, **kwargs)
        self.repo = repo
        self.ctx = ctx
        self.saved_query_group_map = saved_query_group_map

        # If set, all saved query stats will reload on refresh. Otherwise, only
        # stats on the current query will refresh.
        self.do_full_refresh = False

        # saved query name -> query stats Text object
        #
        # A cache used to implement partial refreshes (i.e. when
        # `self.do_full_refresh` is False).
        self._text_cache: dict[str, Text] = {}

    def render(self) -> Panel:
        """Render the statistics widget."""
        query_group = self.saved_query_group_map.get(
            self.ctx.group_name, _DEFAULT_QUERY_GROUP
        )
        stats_query_map = query_group["queries"].copy()

        text = Text()
        max_name_size = max(
            len(name.strip()) for name in stats_query_map.keys()
        )
        if not any(
            query == self.ctx.query for query in stats_query_map.values()
        ):
            stats_query_map.update({"\n::": self.ctx.query})

        for i, (name, query) in enumerate(stats_query_map.items()):
            saved_q_matches_current_q = bool(self.ctx.query == query)
            if saved_q_matches_current_q:
                style = "bold italic blue"
            else:
                style = ""

            extra_text = self._text_cache.get(name)
            if (
                saved_q_matches_current_q
                or extra_text is None
                or self.do_full_refresh
            ):
                pretty_name = name if "\n" in name else f"({i}) {name.upper()}"
                spaces = ""
                if (size := len(pretty_name.strip())) < max_name_size + 1:
                    spaces += (max_name_size - size) * " "
                pretty_name += ":"
                pretty_name += spaces

                tag = GreatTag.from_query(query)
                todos = self.repo.get_by_tag(tag).unwrap()
                group = StatsGroup.from_todos(todos)

                if group.done_stats.count > 0 and group.open_stats.count > 0:
                    xo_string = (
                        f"X({group.done_stats.count}.{group.done_stats.points})"
                        " + "
                        f"O({group.open_stats.count}.{group.open_stats.points})"
                        " = "
                        f"XO({group.all_stats.count}.{group.all_stats.points})"
                    )
                elif group.done_stats.count > 0:
                    stats = group.done_stats
                    xo_string = f"X({stats.count}.{stats.points})"
                elif group.open_stats.count > 0:
                    stats = group.open_stats
                    xo_string = f"O({stats.count}.{stats.points})"
                else:
                    xo_string = "XO"
                extra_text = Text(f"{pretty_name}  {xo_string}\n")
                self._text_cache[name] = extra_text
            extra_text.style = style
            text.append_text(extra_text)

        self.do_full_refresh = False
        return Panel(text, title="Statistics")


@dataclass
class StatsGroup:
    """Todo query stats group.

    Attributes:
        all_stats: Stats on all todos matching this query.
        done_stats: Stats on all completed todos matching this query.
        open_stats: Stats on all un-completed (i.e. not done) todos matching
          this query.
    """

    all_stats: Stats
    done_stats: Stats
    open_stats: Stats

    @classmethod
    def from_todos(cls, todos: Sequence[GreatTodo] | None) -> StatsGroup:
        """Constructs a StatsGroup from an iterable of todos (or None)."""
        if todos is not None:
            all_todos = todos
        else:
            all_todos = []

        all_count = len(all_todos)
        all_points = sum(
            int(todo.metadata.get("p" if todo.done else "xp", "0"))
            for todo in all_todos
        )

        done_todos = [todo for todo in all_todos if todo.done]
        done_count = len(done_todos)
        done_points = sum(
            int(todo.metadata.get("p", "0")) for todo in done_todos
        )

        open_todos = [todo for todo in all_todos if not todo.done]
        open_count = len(open_todos)
        open_points = sum(
            int(todo.metadata.get("xp", "0")) for todo in open_todos
        )

        all_stats = Stats(count=all_count, points=all_points)
        done_stats = Stats(count=done_count, points=done_points)
        open_stats = Stats(count=open_count, points=open_points)
        return cls(
            all_stats=all_stats, done_stats=done_stats, open_stats=open_stats
        )


@dataclass
class Stats:
    """Todo query stats.

    Attributes:
        count: number of todos matched by this query.
        points: Sum of points (i.e. 'p') or expected points (i.e. 'xp') for
          todos matching this query.
    """

    count: int
    points: int


@dataclass
class Context:
    """Mutable TUI Context.

    Used to preserve state after closing the GreatApp instance, running vim,
    and then opening a new GreatApp instance.

    Attributes:
        query: The active todo query string.
        group_name: The name of the saved query group to use. This controls
          which queries are bound to digits (i.e. 0-9) and shown in the stats
          panel.
        edit_todos: After closing the TUI, should we open up vim to edit
          matching todos?
    """

    query: str
    group_name: str
    edit_todos: bool = False


class GreatApp(App[str]):
    """Textual TUI Application Class."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 10;
        grid-gutter: 2;
        padding: 2;
    }
    #stats {
        height: 100%;
        column-span: 3;
        row-span: 9;
    }
    #main {
        height: 100%;
        column-span: 7;
        row-span: 9;
    }
    #command {
        column-span: 10;
        row-span: 1;
    }
    """

    BINDINGS = [
        Binding(
            "escape",
            "change_mode('normal')",
            description="Normal Mode",
            priority=True,
        ),
        Binding(
            "enter", "submit", description="Submit", priority=True, show=False
        ),
    ]

    def __init__(
        self,
        *,
        repo: TaggedRepo[str, GreatTodo, GreatTag],
        ctx: Context,
        saved_query_group_map: SavedQueryGroupMap,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.repo = repo
        self.ctx = ctx
        self.saved_query_group_map = saved_query_group_map

        self.query_widget = Input(
            name="query", id="query", value=self.ctx.query
        )
        self.command_widget = Input(name="command", id="command")

        self.todo_widget = Static(
            Panel(
                _todo_lines_from_query(self.repo, self.ctx.query),
                title="Todos",
            ),
            name="todo",
            id="todo",
        )
        self.stats_widget = StatsWidget(
            self.repo, self.ctx, self.saved_query_group_map, id="stats"
        )

    def compose(self) -> ComposeResult:
        """Yields great widgets."""
        yield GreatHeader()
        yield self.stats_widget
        yield Vertical(self.query_widget, self.todo_widget, id="main")
        yield self.command_widget
        yield GreatFooter()

    async def on_load(self) -> None:
        """Configure key bindings."""
        await self.bind_saved_queries(self.ctx.group_name)
        for ch, group_name in zip(
            "!@#$%^&*()", self.saved_query_group_map.keys()
        ):
            self.bind(ch, f"change_query_group('{group_name}')", show=False)

        self.bind("a", "add_todo", description="Add Todo")
        self.bind("e", "edit", description="Edit Todos")
        self.bind("i", "change_mode('insert')", description="Insert Mode")
        self.bind("I", "clear_and_insert", description="Clear and Insert")
        self.bind("r", "refresh", description="Refresh")
        self.bind("q", "quit", description="Quit")

    async def bind_saved_queries(self, group_name: str) -> None:
        """Binds saved queries in `group_name` to digits (i.e. 0-9)."""
        for i, (name, query) in enumerate(
            self.saved_query_group_map.get(group_name, _DEFAULT_QUERY_GROUP)[
                "queries"
            ].items()
        ):
            if i > 9:
                break

            query = query.replace(")", _FAKE_RIGHT_PAREN)
            description = f"{name.upper()} Query"
            self.bind(
                str(i),
                f"new_query('{query}')",
                description=description,
                show=False,
            )

    async def on_mount(self) -> None:
        """Configure layout."""
        # do a full refresh of this widget every _REFRESH_INTERVAL seconds
        self.set_interval(_REFRESH_INTERVAL, self.action_refresh)

    async def action_add_todo(self) -> None:
        """Action to add a new todo to the inbox."""
        self.command_widget.focus()

    async def action_change_mode(self, mode: str) -> None:
        """Action to toggle to/from insert mode and other modes."""
        self.query_widget.refresh()
        if mode == "insert":
            self.query_widget.focus()
        elif mode == "normal":
            self.stats_widget.focus()
        else:
            raise AssertionError(f"Bad mode: {mode!r}")

    async def action_change_query_group(self, group_name: str) -> None:
        """Changes the saved query group that is being used."""
        # abort early if no query group change is required
        if self.ctx.group_name == group_name:
            return

        self.ctx.group_name = group_name
        self.stats_widget.do_full_refresh = True
        await self.bind_saved_queries(group_name)
        query = get_default_query(self.saved_query_group_map, group_name)
        await self.action_new_query(query)

    async def action_clear_and_insert(self) -> None:
        """Clears input bar and enters Insert mode."""
        self.query_widget.value = ""
        await self.action_change_mode("insert")

    async def action_edit(self) -> None:
        """Edits todos which match the current todo query."""
        self.ctx.edit_todos = True
        await self.action_quit()

    async def action_new_query(self, query: str) -> None:
        """Execute a new todo query."""
        query = query.replace(_FAKE_RIGHT_PAREN, ")")
        self.query_widget.value = query
        await self.action_submit()

    async def action_refresh(self) -> None:
        """Full refresh of TUI (e.g. stats + main panel will reload)."""
        # refresh stats panel
        self.stats_widget.do_full_refresh = True
        self.stats_widget.refresh()

        # refresh main panel
        text = _todo_lines_from_query(self.repo, self.ctx.query)
        self.todo_widget.update(Panel(text, title="Todo List"))

    async def action_submit(self) -> None:
        """Executes the current todo query shown in the input bar."""
        todo_line = self.command_widget.value
        self.command_widget.value = ""
        if todo_line != "":
            todo = GreatTodo.from_line(todo_line).unwrap()
            self.repo.add(todo)
            self.stats_widget.do_full_refresh = True

        self.ctx.query = self.query_widget.value
        self.stats_widget.refresh()
        text = _todo_lines_from_query(self.repo, self.ctx.query)
        self.todo_widget.update(Panel(text, title="Todo List"))
        await self.action_change_mode("normal")


def _todo_lines_from_query(
    repo: TaggedRepo[str, GreatTodo, GreatTag], query: str
) -> str:
    tag = GreatTag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()

    result = ""
    for todo in sorted(todos):
        result += todo.to_line() + "\n"

    return result


# TODO(bugyi): Convert to a method of a new SavedQueryGroupManager type.
def get_default_query(
    saved_query_group_map: SavedQueryGroupMap, group_name: str
) -> str:
    """Returns the name of the configured default query for a query group.

    Helper function that hides the details of parsing the SavedQueryGroup data
    structure.

    Args:
        saved_query_group_map: Contains the query group we are interested in.
        group_name: Name of the query group we are interested in.
    """
    query_group = saved_query_group_map.get(group_name, _DEFAULT_QUERY_GROUP)
    default_key = query_group["default"]
    queries = query_group["queries"] if query_group["queries"] else {"all": ""}
    if default_key not in queries:
        default_key = list(queries.keys())[0]
    query = queries[default_key]
    return query
