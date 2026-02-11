"""Log file viewer."""

from __future__ import annotations

from pathlib import Path

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class LogViewScreen(Screen):
    """Scrollable view of a log file."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self, log_path: Path) -> None:
        super().__init__()
        self.log_path = log_path

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"[bold]Log:[/bold] {self.log_path.name}",
            classes="source-header",
        )
        yield VerticalScroll(id="source-scroll")
        yield Footer()

    def on_mount(self) -> None:
        try:
            content = self.log_path.read_text()
        except Exception as exc:
            content = f"(could not read log: {exc})"

        syntax = Syntax(
            content,
            "text",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        container = self.query_one("#source-scroll")
        container.mount(Static(syntax, id="source-code"))

    def action_go_back(self) -> None:
        self.app.pop_screen()
