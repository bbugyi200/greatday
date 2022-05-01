"""Functions / classes used to create greatday's TUI."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.reactive import Reactive
from textual.widgets import Footer, Header, Static
from textual_inputs import TextInput

from ._repo import GreatRepo
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

        tag = Tag.from_query("@inbox")
        inbox_todos = self.repo.get_by_tag(tag).unwrap()
        inbox_count = len(inbox_todos) if inbox_todos else 0

        tickler_count = 0

        tag = Tag.from_query("@today done=0")
        today_todos = self.repo.get_by_tag(tag).unwrap()
        today_count = len(today_todos) if today_todos else 0

        return Panel(
            f"INBOX: {inbox_count}\nTICKLERS: {tickler_count}\nTODAY:"
            f" {today_count}\n",
            title="Statistics",
        )


class GreatApp(App):
    """Textual TUI Application Class."""

    def __init__(self, *, repo: GreatRepo, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.repo = repo

        self.input_widget = TextInput(name="input", placeholder="@today")
        self.main_widget = Static(
            Panel(_todo_lines_from_query(self.repo, "@today"), title="Main"),
            name="main",
        )
        self.stats_widget = StatsWidget(self.repo)

    async def on_load(self) -> None:
        """Configure key bindings."""
        await self.bind("escape", "change_mode('normal')", "Normal Mode")
        await self.bind("enter", "submit", "Submit")
        await self.bind("i", "change_mode('insert')", "Insert Mode")
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

    async def action_submit(self) -> None:
        """Called when the user hits <Enter>."""
        text = _todo_lines_from_query(self.repo, self.input_widget.value)
        await self.main_widget.update(Panel(text, title="Todo List"))


def _todo_lines_from_query(repo: GreatRepo, query: str) -> str:
    tag = Tag.from_query(query)
    todos = repo.get_by_tag(tag).unwrap()

    result = ""
    for todo in sorted(todos):
        result += todo.to_line() + "\n"

    return result


def start_textual_app(repo: GreatRepo) -> None:
    """Starts the TUI using the GreatApp class."""
    GreatApp.run(repo=repo, title="Greatday TUI", log="greatday_textual.log")
