"""Post-execution summary screen."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from brotherly.models import QueuedTask, TaskStatus


class SummaryScreen(Screen):
    """Shows execution results after a script completes."""

    BINDINGS = [
        Binding("enter", "dismiss", "Continue"),
        Binding("escape", "dismiss", "Continue"),
        Binding("l", "view_log", "View Log"),
    ]

    def __init__(self, completed_task: QueuedTask, log_path: Path) -> None:
        super().__init__()
        self.completed_task = completed_task
        self.log_path = log_path

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="summary-scroll"):
            success = self.completed_task.status == TaskStatus.COMPLETED

            if success:
                yield Static(
                    "[bold green on dark_green]  ✓ COMPLETED SUCCESSFULLY  [/bold green on dark_green]",
                    classes="summary-banner",
                )
            else:
                yield Static(
                    f"[bold white on red]  ✗ FAILED (exit code {self.completed_task.exit_code})  [/bold white on red]",
                    classes="summary-banner",
                )

            yield Static(
                f"\n[bold]{self.completed_task.title}[/bold]",
                classes="summary-title",
            )

            yield Static(
                f"[dim]Log: {self.log_path}[/dim]",
                classes="summary-meta",
            )

            # Show last few lines of log
            yield Static("", classes="spacer")
            yield Static("[bold]Log tail:[/bold]", classes="summary-label")

            log_tail = self._read_log_tail()
            yield Static(
                f"[dim]{log_tail}[/dim]",
                id="log-tail",
                classes="log-tail",
            )

            yield Static("", classes="spacer")
            yield Static(
                "[dim]Chris is being notified in the background.[/dim]",
                classes="summary-notify",
            )

            yield Static("", classes="spacer")
            with Center(classes="button-row"):
                with Horizontal(classes="buttons"):
                    yield Button("View Log", variant="default", id="btn-log")
                    yield Button("Continue", variant="primary", id="btn-continue")

        yield Footer()

    def _read_log_tail(self, lines: int = 15) -> str:
        try:
            content = self.log_path.read_text()
            all_lines = content.splitlines()
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "\n".join(tail)
        except Exception:
            return "(could not read log)"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-continue":
            self.action_dismiss()
        elif event.button.id == "btn-log":
            self.action_view_log()

    def action_dismiss(self) -> None:
        self.app.exit()

    def action_view_log(self) -> None:
        """Show full log in a scrollable view."""
        from brotherly.screens.log_view import LogViewScreen

        self.app.push_screen(LogViewScreen(self.log_path))
