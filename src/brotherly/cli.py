"""CLI entry points for brotherly."""

from __future__ import annotations

from pathlib import Path

import click

from brotherly.config import Config
from brotherly.models import QueuedTask
from brotherly.queue import QueueManager


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Brotherly - Trust-based remote administration."""
    if ctx.invoked_subcommand is None:
        from brotherly.app import BrotherlyApp

        app = BrotherlyApp()
        app.run()


@main.command()
@click.argument("script", type=click.Path(exists=True, path_type=Path))
@click.option("--title", "-t", required=True, help="Short title for the task")
@click.option("--description", "-d", required=True, help="What this script does")
@click.option("--sudo", is_flag=True, help="Script requires sudo")
def queue(script: Path, title: str, description: str, sudo: bool) -> None:
    """Queue a script for review and execution."""
    config = Config.load()
    mgr = QueueManager(config)
    task = mgr.add_task(script, title, description, requires_sudo=sudo)

    click.secho(f"  Queued: {task.title}", fg="green")
    click.echo(f"  ID: {task.id}")
    click.echo(f"  Script: {task.script_filename}")


@main.command(name="list")
@click.option("--all", "show_all", is_flag=True, help="Show all tasks, not just pending")
def list_tasks(show_all: bool) -> None:
    """List queued tasks."""
    config = Config.load()
    mgr = QueueManager(config)
    tasks = mgr.list_all() if show_all else mgr.list_pending()

    if not tasks:
        click.echo("No tasks queued.")
        return

    for task in tasks:
        status_colors = {
            "pending": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }
        color = status_colors.get(task.status.value, "white")
        click.secho(f"  [{task.status.value:>9}] ", fg=color, nl=False)
        click.echo(f"{task.title} ({task.age})")
        click.echo(f"             {task.description[:60]}")
