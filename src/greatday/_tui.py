"""Functions / classes used to create greatday's TUI."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from functools import partial
from typing import Any

import magodo
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.reactive import Reactive
from textual.widgets import Footer, Header, Static
from textual_inputs import TextInput
from typist import PathLike

from ._editor import edit_and_commit_todos
from ._repo import GreatRepo
from ._session import GreatSession
from ._tag import Tag


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
            key_display = (
                binding.key.upper()
                if binding.key_display is None
                else binding.key_display
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

    repo: Reactive[GreatRepo | None] = Reactive(None)

    def __init__(self, repo: GreatRepo, *args: Any, **kwargs: Any) -> None:
        super().__init__("", *args, **kwargs)
        self.repo = repo

    def render(self) -> Panel:
        """Render the statistics widget."""
        assert self.repo is not None

        tag = Tag.from_query("@inbox done=0")
        inbox_todos = self.repo.get_by_tag(tag).unwrap()
        inbox_count = len(inbox_todos) if inbox_todos else 0

        today = dt.date.today()
        tag = Tag.from_query(
            "tickle<={0} snooze?<={0} done=0".format(magodo.from_date(today))
        )
        tickler_todos = self.repo.get_by_tag(tag).unwrap()
        tickler_count = len(tickler_todos) if tickler_todos else 0

        tag = Tag.from_query("@today snooze?<=0d done=0")
        today_todos = self.repo.get_by_tag(tag).unwrap()
        today_count = len(today_todos) if today_todos else 0

        return Panel(
            f"INBOX: {inbox_count}\nTICKLERS: {tickler_count}\nTODAY:"
            f" {today_count}\n",
            title="Statistics",
        )


@dataclass
class Context:
    """Mutable TUI Context.

    Used to preserve state after closing the GreatApp instance, running vim,
    and then opening a new GreatApp instance.

    Attributes:
        query: The active todo query string.
        is_user_query: Is this query one the user selected or just the
          default?
        edit_todos: After closing the TUI, should we open up vim to edit
          matching todos?
    """

    query: str
    is_user_query: bool = False
    edit_todos: bool = False


class GreatApp(App):
    """Textual TUI Application Class."""

    def __init__(
        self, *, repo: GreatRepo, ctx: Context, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        self.repo = repo
        self.ctx = ctx

        text_input = partial(TextInput, name="input")
        if ctx.is_user_query:
            self.input_widget = text_input(value=self.ctx.query)
        else:
            self.input_widget = text_input(placeholder=self.ctx.query)

        cursor = (
            "|",
            Style(
                color="black",
                blink=True,
                bold=True,
            ),
        )
        self.input_widget.cursor = cursor

        self.main_widget = Static(
            Panel(
                _todo_lines_from_query(self.repo, self.ctx.query),
                title="Main",
            ),
            name="main",
        )
        self.stats_widget = StatsWidget(self.repo)

    async def on_load(self) -> None:
        """Configure key bindings."""
        await self.bind("escape", "change_mode('normal')", "Normal Mode")
        await self.bind("enter", "submit", "Submit")
        await self.bind("e", "edit", "Edit Todos")
        await self.bind("i", "change_mode('insert')", "Insert Mode")
        await self.bind(
            "I", "change_mode('INSERT')", "Erase and Insert Mode", show=False
        )
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        """Configure layout."""
        # configure header and footer...
        await self.view.dock(GreatHeader(), edge="top")
        await self.view.dock(GreatFooter(), edge="bottom")

        # configure other widgets...
        await self.view.dock(self.input_widget, edge="bottom", size=10)
        await self.view.dock(self.stats_widget, edge="left", size=50)
        await self.view.dock(self.main_widget, edge="top")

    async def action_change_mode(self, mode: str) -> None:
        """Action to toggle to/from insert mode and other modes."""
        if mode.lower() == "insert":
            self.input_widget.title = "INSERT"

            # Clear the input bar's value if mode == 'INSERT'...
            if mode.isupper():
                self.input_widget.value = ""

            self.input_widget.refresh()
            await self.input_widget.focus()
        elif mode.lower() == "normal":
            self.input_widget.title = ""
            self.input_widget.refresh()
            await self.main_widget.focus()
        else:
            raise AssertionError(f"Bad mode: {mode!r}")

    async def action_submit(self) -> None:
        """Called when the user hits <Enter>."""
        self.ctx.query = self.input_widget.value
        self.ctx.is_user_query = True
        self.input_widget.placeholder = ""
        text = _todo_lines_from_query(self.repo, self.ctx.query)
        await self.main_widget.update(Panel(text, title="Todo List"))
        await self.action_change_mode("normal")

    async def action_edit(self) -> None:
        """Edits todos which match the current todo query."""
        self.ctx.edit_todos = True
        await self.action_quit()


def _todo_lines_from_query(repo: GreatRepo, query: str) -> str:
    tag = Tag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()

    result = ""
    for todo in sorted(todos):
        result += todo.to_line() + "\n"

    return result


def start_textual_app(data_dir: PathLike, repo_path: PathLike) -> None:
    """Starts the TUI using the GreatApp class."""
    repo = GreatRepo(data_dir, repo_path)
    ctx = Context("@today snooze?<=0d")
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
        with GreatSession(data_dir, repo_path, tag) as session:
            edit_and_commit_todos(session)

        ctx.edit_todos = False
        run_app()
