"""Main screen showing pending tasks."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from brotherly.models import QueuedTask


class TaskListItem(ListItem):
    """A single task in the list."""

    def __init__(self, queued_task: QueuedTask) -> None:
        super().__init__()
        self.queued_task = queued_task

    def compose(self) -> ComposeResult:
        sudo_badge = " [sudo]" if self.queued_task.requires_sudo else ""
        yield Static(
            f"[bold]{self.queued_task.title}[/bold]{sudo_badge}",
            classes="task-title",
        )
        yield Static(
            f"[dim]{self.queued_task.description[:80]}[/dim]",
            classes="task-desc",
        )
        yield Static(
            f"[dim italic]Queued by {self.queued_task.queued_by} \u2022 {self.queued_task.age}[/dim italic]",
            classes="task-meta",
        )


class TaskListScreen(Screen):
    """Main screen listing all pending tasks."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="task-container")
        yield Footer()

    def on_mount(self) -> None:
        self.load_tasks()

    def load_tasks(self) -> None:
        container = self.query_one("#task-container")
        container.remove_children()

        tasks = self.app.queue.list_pending()

        if not tasks:
            container.mount(
                Vertical(
                    Center(
                        Static(
                            "[dim]No tasks queued.[/dim]\n\n"
                            "[dim italic]When Chris queues something, it'll show up here.[/dim italic]",
                            classes="empty-state",
                        ),
                    ),
                    id="empty-wrapper",
                )
            )
            return

        items = [TaskListItem(task) for task in tasks]
        container.mount(ListView(*items, id="task-list"))

    @on(ListView.Selected)
    def on_task_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, TaskListItem):
            from brotherly.screens.task_detail import TaskDetailScreen

            self.app.push_screen(TaskDetailScreen(event.item.queued_task))

    def action_refresh(self) -> None:
        self.load_tasks()
