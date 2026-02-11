"""Source code viewer with syntax highlighting."""

from __future__ import annotations

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from brotherly.models import QueuedTask


class SourceViewScreen(Screen):
    """Syntax-highlighted view of the queued script."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self, queued_task: QueuedTask) -> None:
        super().__init__()
        self.queued_task = queued_task

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"[bold]Source:[/bold] {self.queued_task.script_filename}",
            classes="source-header",
        )
        yield VerticalScroll(id="source-scroll")
        yield Footer()

    def on_mount(self) -> None:
        source = self.app.queue.get_script_content(self.queued_task)
        syntax = Syntax(
            source,
            "bash",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        container = self.query_one("#source-scroll")
        container.mount(Static(syntax, id="source-code"))

    def action_go_back(self) -> None:
        self.app.pop_screen()
