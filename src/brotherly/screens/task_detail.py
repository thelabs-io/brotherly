"""Task detail screen with description and actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Markdown, Static

from brotherly.models import QueuedTask


class TaskDetailScreen(Screen):
    """Shows full task details with action buttons."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "run_task", "Run"),
        Binding("v", "view_source", "View Source"),
    ]

    def __init__(self, queued_task: QueuedTask) -> None:
        super().__init__()
        self.queued_task = queued_task

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="detail-scroll"):
            yield Static(f"[bold]{self.queued_task.title}[/bold]", classes="detail-title")

            # Metadata badges
            badges = f"[dim]Queued by [bold]{self.queued_task.queued_by}[/bold] \u2022 {self.queued_task.age}[/dim]"
            if self.queued_task.requires_sudo:
                badges += "  [bold on dark_orange3] SUDO [/bold on dark_orange3]"
            yield Static(badges, classes="detail-meta")

            yield Static("", classes="spacer")
            yield Markdown(self.queued_task.description, id="detail-description")
            yield Static("", classes="spacer")

            with Center(classes="button-row"):
                with Horizontal(classes="buttons"):
                    yield Button("Run", variant="success", id="btn-run")
                    yield Button("View Source", variant="primary", id="btn-source")
                    yield Button("Back", variant="default", id="btn-back")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            self.action_run_task()
        elif event.button.id == "btn-source":
            self.action_view_source()
        elif event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_view_source(self) -> None:
        from brotherly.screens.source_view import SourceViewScreen

        self.app.push_screen(SourceViewScreen(self.queued_task))

    def action_run_task(self) -> None:
        from brotherly.screens.execution import ExecutionScreen

        self.app.push_screen(ExecutionScreen(self.queued_task))
