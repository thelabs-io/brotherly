"""Source code viewer with syntax highlighting."""

from __future__ import annotations

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

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
        with Center(classes="button-row"):
            with Horizontal(classes="buttons"):
                yield Button("Back", variant="default", id="btn-back")
        yield Footer()

    def on_mount(self) -> None:
        from brotherly.script_parser import parse_script_header

        script_path = self.app.requests.get_script_path(self.queued_task)
        header = parse_script_header(script_path)
        full_content = script_path.read_text()
        lines = full_content.splitlines()
        code_lines = lines[header.body_start_line:]
        source = "\n".join(code_lines)

        syntax = Syntax(
            source,
            "bash",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        container = self.query_one("#source-scroll")
        container.mount(Static(syntax, id="source-code"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()
