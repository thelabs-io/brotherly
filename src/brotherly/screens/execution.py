"""Execution screen with live output and notifications."""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from brotherly.models import QueuedTask
from brotherly.notify import notify_chris
from brotherly.runner import run_script


class ExecutionScreen(Screen):
    """Runs the script with live output display."""

    BINDINGS = [
        Binding("escape", "maybe_back", "Back", show=False),
    ]

    def __init__(self, queued_task: QueuedTask) -> None:
        super().__init__()
        self.queued_task = queued_task
        self.running = False
        self.finished = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="exec-container"):
            yield Static(
                f"[bold]Running:[/bold] {self.queued_task.title}",
                classes="exec-title",
            )
            yield Static("", id="exec-status", classes="exec-status")
            yield RichLog(
                id="exec-output",
                highlight=True,
                markup=True,
                wrap=True,
            )
            with Center(id="exec-buttons", classes="button-row"):
                yield Button(
                    "Confirm & Run",
                    variant="warning",
                    id="btn-confirm",
                )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#exec-status").update(
            "[bold yellow]Ready to execute. Press Confirm to proceed.[/bold yellow]"
        )
        output = self.query_one("#exec-output", RichLog)
        output.write("[dim]Script output will appear here...[/dim]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.start_execution()
        elif event.button.id == "btn-done":
            self.action_go_back()

    def start_execution(self) -> None:
        self.running = True
        btn = self.query_one("#btn-confirm", Button)
        btn.disabled = True
        btn.display = False

        output = self.query_one("#exec-output", RichLog)
        output.clear()

        self.query_one("#exec-status").update(
            "[bold blue]Running...[/bold blue]"
        )
        self.execute_task()

    @work(thread=False)
    async def execute_task(self) -> None:
        output = self.query_one("#exec-output", RichLog)

        def on_output(line: str) -> None:
            self.app.call_from_thread(output.write, line)

        exit_code = await run_script(
            self.queued_task,
            self.app.queue,
            self.app.config,
            on_output=on_output,
        )

        self.running = False
        self.finished = True

        success = exit_code == 0
        status = self.query_one("#exec-status")

        if success:
            status.update(
                "[bold green on dark_green] COMPLETED SUCCESSFULLY [/bold green on dark_green]"
            )
        else:
            status.update(
                f"[bold white on red] FAILED (exit code {exit_code}) [/bold white on red]"
            )

        # Send notifications
        output.write("")
        output.write("[dim]Notifying Chris...[/dim]")

        log_path = self.app.queue.log_path(self.queued_task)
        notified = await notify_chris(
            self.queued_task,
            log_path,
            self.app.config,
            on_status=lambda msg: self.app.call_from_thread(
                output.write, f"[dim]  {msg}[/dim]"
            ),
        )

        if notified:
            output.write("[dim green]  All notifications sent.[/dim green]")
        else:
            output.write("[dim red]  Some notifications failed (check SSH connectivity).[/dim red]")

        # Show done button
        buttons = self.query_one("#exec-buttons", Center)
        await buttons.mount(
            Button("Done", variant="primary", id="btn-done")
        )

    def action_maybe_back(self) -> None:
        if not self.running:
            self.action_go_back()

    def action_go_back(self) -> None:
        # Pop back to the task list (removing execution + detail screens)
        # Stack: default Screen → TaskListScreen → TaskDetailScreen → ExecutionScreen
        # We want to keep default + TaskListScreen (stack size 2)
        while len(self.app.screen_stack) > 2:
            self.app.pop_screen()
