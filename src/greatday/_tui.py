"""Functions / classes used to create greatday's TUI."""

from __future__ import annotations

from textual.app import App


class GreatApp(App):
    """Textual TUI Application Class."""


def start_textual_app() -> None:
    """Starts the TUI using the GreatApp class."""
    GreatApp.run()
