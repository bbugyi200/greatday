"""Functions / classes used to create greatday's TUI."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any, Final, Iterator, Sequence

from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.widgets import Footer, Header, Static
from textual_inputs import TextInput
from typist import PathLike
from vimala import vim

from ._common import CTX_FIRST, CTX_INBOX, CTX_LAST, CTX_TODAY
from ._repo import GreatRepo
from ._session import GreatSession
from ._tag import Tag
from ._todo import GreatTodo


_TICKLER_QUERY: Final = "tickle<=0d !snooze"
INBOX_QUERY: Final = f"@{CTX_INBOX} done=0"
FIRST_QUERY: Final = f"@{CTX_FIRST} {_TICKLER_QUERY}"
LAST_QUERY: Final = f"@{CTX_LAST} {_TICKLER_QUERY}"
TODAY_QUERY: Final = f"@{CTX_TODAY}"

# A mapping of names to queries that will be displayed in the "Stats" textual
# panel.
STATS_QUERY_MAP: dict[str, str] = {
    "inbox": INBOX_QUERY,
    "first": FIRST_QUERY,
    "today": TODAY_QUERY,
    "last": LAST_QUERY,
}


class GreatHeader(Header):
    """Override the default Header for Styling"""

    def __init__(self) -> None:
        super().__init__()
        self.tall = False
        self.style = Style(color="white", bgcolor="rgb(98,98,98)")

    def render(self) -> Table:
        """Returns renderable header."""
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.add_column(justify="left", ratio=0, width=8)
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("clock", justify="right", width=8)
        header_table.add_row(
            "🔤", self.full_title, self.get_clock() if self.clock else ""
        )
        return header_table


class GreatFooter(Footer):
    """Override the default Footer for Styling"""

    def make_key_text(self) -> Text:
        """Create text containing all the keys."""
        text = Text(
            style="white on rgb(98,98,98)",
            no_wrap=True,
            overflow="ellipsis",
            justify="left",
            end="",
        )
        for binding in self.app.bindings.shown_keys:
            key = binding.key.upper() if len(binding.key) > 1 else binding.key
            key_display = (
                key if binding.key_display is None else binding.key_display
            )
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (
                    f" {key_display} ",
                    "reverse" if hovered else "default on default",
                ),
                f" {binding.description} ",
                meta={
                    "@click": f"app.press('{binding.key}')",
                    "key": binding.key,
                },
            )
            text.append_text(key_text)
        return text


class StatsWidget(Static):
    """Widget that shows Todo statistics."""

    def __init__(
        self, repo: GreatRepo, ctx: Context, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__("", *args, **kwargs)
        self.repo = repo
        self.ctx = ctx

    def render(self) -> Panel:
        """Render the statistics widget."""
        assert self.repo is not None

        stats_query_map = STATS_QUERY_MAP.copy()
        stats_query_map.update({"\ncurrent": self.ctx.query})

        text = ""
        max_name_size = max(
            len(name.strip()) for name in stats_query_map.keys()
        )
        for name, query in stats_query_map.items():
            tag = Tag.from_query(query)
            todos = self.repo.get_by_tag(tag).unwrap()
            group = StatsGroup.from_todos(todos)

            pretty_name = name.upper()
            spaces = ""
            if (size := len(pretty_name.strip())) < max_name_size + 1:
                spaces += (max_name_size - size) * " "
            pretty_name += ":"
            pretty_name += spaces

            text += (
                f"{pretty_name}   "
                f"{group.done_stats.count}.{group.done_stats.points} / "
                f"{group.all_stats.count}.{group.all_stats.points}\n"
            )

        return Panel(text, title="Statistics")


@dataclass
class StatsGroup:
    all_stats: Stats
    done_stats: Stats

    @classmethod
    def from_todos(cls, todos: Sequence[GreatTodo] | None) -> StatsGroup:
        """Constructs a StatsGroup from an iterable of todos (or None)."""
        if todos is not None:
            all_todos = todos
        else:
            all_todos = []

        all_count = len(all_todos)
        all_points = sum(
            int(todo.metadata.get("p", "0")) for todo in all_todos
        )

        done_todos = [todo for todo in all_todos if todo.done]
        done_count = len(done_todos)
        done_points = sum(
            int(todo.metadata.get("p", "0")) for todo in done_todos
        )

        all_stats = Stats(count=all_count, points=all_points)
        done_stats = Stats(count=done_count, points=done_points)
        return cls(all_stats=all_stats, done_stats=done_stats)


@dataclass
class Stats:
    count: int
    points: int


@dataclass
class Context:
    """Mutable TUI Context.

    Used to preserve state after closing the GreatApp instance, running vim,
    and then opening a new GreatApp instance.

    Attributes:
        query: The active todo query string.
        edit_todos: After closing the TUI, should we open up vim to edit
          matching todos?
    """

    query: str
    edit_todos: bool = False


class GreatApp(App):
    """Textual TUI Application Class."""

    def __init__(
        self, *, repo: GreatRepo, ctx: Context, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        self.repo = repo
        self.ctx = ctx

        text_input_cursor = (
            "|",
            Style(
                color="black",
                blink=True,
                bold=True,
            ),
        )
        self.input_widget = TextInput(name="input", value=self.ctx.query)
        self.input_widget.cursor = text_input_cursor

        self.main_widget = Static(
            Panel(
                _todo_lines_from_query(self.repo, self.ctx.query),
                title="Main",
            ),
            name="main",
        )
        self.stats_widget = StatsWidget(self.repo, self.ctx)

    async def on_load(self) -> None:
        """Configure key bindings."""
        n = _counter(start=1)
        await self.bind(next(n), f"new_query('{INBOX_QUERY}')", "INBOX Query")
        await self.bind(next(n), f"new_query('{FIRST_QUERY}')", "FIRST Query")
        await self.bind(next(n), f"new_query('{TODAY_QUERY}')", "TODAY Query")
        await self.bind(next(n), f"new_query('{LAST_QUERY}')", "LAST Query")
        await self.bind("escape", "change_mode('normal')", "Normal Mode")
        await self.bind("enter", "submit", "Submit")
        await self.bind("e", "edit", "Edit Todos")
        await self.bind("i", "change_mode('insert')", "Insert Mode")
        await self.bind("I", "clear_and_insert", "Clear and Insert")
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        """Configure layout."""
        # configure header and footer...
        await self.view.dock(GreatHeader(), edge="top")
        await self.view.dock(GreatFooter(), edge="bottom")

        # configure other widgets...
        await self.view.dock(self.input_widget, edge="bottom", size=5)
        await self.view.dock(self.stats_widget, edge="left", size=50)
        await self.view.dock(self.main_widget, edge="top")

    async def action_change_mode(self, mode: str) -> None:
        """Action to toggle to/from insert mode and other modes."""
        if mode == "insert":
            self.input_widget.title = "INSERT"
            self.input_widget.refresh()
            await self.input_widget.focus()
        elif mode == "normal":
            self.input_widget.title = ""
            self.input_widget.refresh()
            await self.main_widget.focus()
        else:
            raise AssertionError(f"Bad mode: {mode!r}")

    async def action_clear_and_insert(self) -> None:
        """Clears input bar and enters Insert mode."""
        self.input_widget.value = ""
        self.input_widget._cursor_position = 0
        await self.action_change_mode("insert")

    async def action_edit(self) -> None:
        """Edits todos which match the current todo query."""
        self.ctx.edit_todos = True
        await self.action_quit()

    async def action_new_query(self, query: str) -> None:
        """Execute a new todo query."""
        self.input_widget.value = query
        self.input_widget._cursor_position = len(query)
        await self.action_submit()

    async def action_submit(self) -> None:
        """Executes the current todo query shown in the input bar."""
        self.ctx.query = self.input_widget.value
        self.stats_widget.refresh()
        text = _todo_lines_from_query(self.repo, self.ctx.query)
        await self.main_widget.update(Panel(text, title="Todo List"))
        await self.action_change_mode("normal")


def _counter(start: int = 1) -> Iterator[str]:
    n = start
    while True:
        yield str(n)
        n += 1


def _todo_lines_from_query(repo: GreatRepo, query: str) -> str:
    tag = Tag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()

    result = ""
    for todo in sorted(todos):
        result += todo.to_line() + "\n"

    return result


def start_textual_app(data_dir: PathLike) -> None:
    """Starts the TUI using the GreatApp class."""
    repo = GreatRepo(data_dir)
    ctx = Context(TODAY_QUERY)
    run_app = partial(
        GreatApp.run,
        repo=repo,
        ctx=ctx,
        title="Greatday TUI",
        log="greatday_textual.log",
    )
    run_app()

    while ctx.edit_todos:
        tag = Tag.from_query(ctx.query)
        with GreatSession(data_dir, tag) as session:
            vim(session.path).unwrap()
            session.commit()

        ctx.edit_todos = False
        run_app()
