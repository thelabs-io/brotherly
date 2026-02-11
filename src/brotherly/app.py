"""Main Textual application."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from brotherly.config import Config
from brotherly.queue import QueueManager
from brotherly.screens.task_list import TaskListScreen


class BrotherlyApp(App):
    """Trust-based remote administration TUI."""

    TITLE = "Brotherly"
    SUB_TITLE = "Remote admin, reviewed by a brother"
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.config = Config.load()
        self.queue = QueueManager(self.config)

    def on_mount(self) -> None:
        self.push_screen(TaskListScreen())
