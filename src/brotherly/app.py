"""Textual applications for brotherly.

Two separate apps that the orchestrator runs in sequence:
- ReviewApp: Matt reviews pending tasks and approves/skips/quits
- SummaryApp: Shows execution results after a script completes
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from brotherly.config import Config
from brotherly.models import QueuedTask
from brotherly.request import RequestManager


class ReviewApp(App):
    """TUI for reviewing pending requests."""

    TITLE = "Brotherly"
    SUB_TITLE = "Pending requests"
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        config: Config | None = None,
        request_manager: RequestManager | None = None,
    ) -> None:
        super().__init__()
        self.config = config or Config.load()
        self.requests = request_manager or RequestManager(self.config)
        self.result: dict | None = None

    def on_mount(self) -> None:
        from brotherly.screens.task_list import TaskListScreen

        self.push_screen(TaskListScreen())

    def run_task(self, task: QueuedTask) -> None:
        """Called by detail screen when Matt chooses to run a request."""
        self.result = {"action": "run", "task_id": task.id, "title": task.title}
        self.exit()

    def skip_task(self) -> None:
        """Called by detail screen when Matt skips a task."""
        self.result = {"action": "skip"}
        self.exit()

    def quit_app(self) -> None:
        """Called when Matt wants to quit entirely."""
        self.result = {"action": "quit"}
        self.exit()


class SummaryApp(App):
    """TUI for showing execution results."""

    TITLE = "Brotherly"
    SUB_TITLE = "Execution complete"
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(self, task: QueuedTask, log_path: Path) -> None:
        super().__init__()
        self.completed_task = task
        self.log_path = log_path

    def on_mount(self) -> None:
        from brotherly.screens.summary import SummaryScreen

        self.push_screen(SummaryScreen(self.completed_task, self.log_path))
