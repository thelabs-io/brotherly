"""Task detail screen with description and approval actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Markdown, Static

from brotherly.models import QueuedTask


class TaskDetailScreen(Screen):
    """Shows full task details. Matt can approve, view source, skip, or go back."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "run", "Run"),
        Binding("v", "view_source", "View Source"),
        Binding("s", "skip", "Skip"),
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
                badges += "  [bold reverse] SUDO [/bold reverse]"
            yield Static(badges, classes="detail-meta")

            yield Static("", classes="spacer")
            yield Markdown(self.queued_task.description, id="detail-description")
            yield Static("", classes="spacer")

            with Center(classes="button-row"):
                with Horizontal(classes="buttons"):
                    yield Button("Run", variant="success", id="btn-run")
                    yield Button("View Source", variant="primary", id="btn-source")
                    yield Button("Skip", variant="warning", id="btn-skip")
                    yield Button("Back", variant="default", id="btn-back")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            self.action_run()
        elif event.button.id == "btn-source":
            self.action_view_source()
        elif event.button.id == "btn-skip":
            self.action_skip()
        elif event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_view_source(self) -> None:
        from brotherly.screens.source_view import SourceViewScreen

        self.app.push_screen(SourceViewScreen(self.queued_task))

    def action_run(self) -> None:
        """Matt runs — TUI exits, orchestrator takes over for execution."""
        self.app.run_task(self.queued_task)

    def action_skip(self) -> None:
        """Skip this task, move to the next one."""
        self.app.skip_task()
