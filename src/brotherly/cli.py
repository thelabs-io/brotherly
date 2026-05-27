"""CLI entry points for brotherly."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import click

from brotherly.config import Config
from brotherly.models import QueuedTask
from brotherly.request import RequestManager
from brotherly.script_parser import parse_script_header


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Brotherly - Transparent remote administration for brothers."""
    if ctx.invoked_subcommand is None:
        from brotherly.orchestrator import run

        run()


@main.command()
@click.argument("script", type=click.Path(exists=True, path_type=Path))
@click.option("--host", "-h", default=None, help="Remote host (SSH config alias)")
@click.option("--sudo", is_flag=True, help="Script requires sudo")
def request(script: Path, host: str | None, sudo: bool) -> None:
    """Send a script request for review and execution."""
    config = Config.load()
    header = parse_script_header(script)

    if not header.title or header.title == script.stem:
        click.secho("  Warning: no title found in script header, using filename.", fg="yellow")

    target = host or config.default_host

    if target:
        _remote_request(config, script, header, target, sudo)
    else:
        mgr = RequestManager(config)
        task = mgr.add_task(script, requires_sudo=sudo)
        click.secho(f"  Requested: {task.title}", fg="green")
        click.echo(f"  ID: {task.id}")


def _remote_request(config, script, header, target, sudo):
    """Send a request to a remote host via SSH."""
    from datetime import datetime

    task_id = QueuedTask.generate_id(header.title)
    script_filename = f"{task_id}.sh"
    remote_dir = config.remote_data_dir + "/requests"

    # Ensure remote directory exists (group-writable for multi-user access)
    ssh_mkdir = subprocess.run(
        ["ssh", target, f"mkdir -p {remote_dir} && chmod g+w {remote_dir}"],
        capture_output=True, text=True, timeout=15,
    )
    if ssh_mkdir.returncode != 0:
        click.secho(f"  Failed to create remote dir: {ssh_mkdir.stderr.strip()}", fg="red")
        return

    # Run prep commands as the requester (chris) before queuing
    if header.prep:
        click.echo(f"  Running prep commands on {target}...")
        ssh_prep = subprocess.run(
            ["ssh", target, header.prep],
            capture_output=True, text=True, timeout=60,
        )
        if ssh_prep.returncode != 0:
            click.secho(f"  Prep failed: {ssh_prep.stderr.strip()}", fg="red")
            if ssh_prep.stdout.strip():
                click.echo(f"  {ssh_prep.stdout.strip()}")
            return
        if ssh_prep.stdout.strip():
            click.echo(f"  {ssh_prep.stdout.strip()}")

    # SCP the script
    remote_path = f"{target}:{remote_dir}/{script_filename}"
    scp = subprocess.run(
        ["scp", str(script), remote_path],
        capture_output=True, text=True, timeout=30,
    )
    if scp.returncode != 0:
        click.secho(f"  Failed to copy script: {scp.stderr.strip()}", fg="red")
        return

    # chmod on remote — group-writable so the approver account can update
    subprocess.run(
        ["ssh", target, f"chmod 775 {remote_dir}/{script_filename}"],
        capture_output=True, timeout=10,
    )

    # Create and send metadata JSON
    task = QueuedTask(
        id=task_id,
        script_filename=script_filename,
        title=header.title,
        description=header.description,
        queued_at=datetime.now().isoformat(),
        requires_sudo=sudo,
    )
    meta_json = task.to_json()

    ssh_meta = subprocess.run(
        ["ssh", target, f"cat > {remote_dir}/{task_id}.json && chmod 664 {remote_dir}/{task_id}.json"],
        input=meta_json, capture_output=True, text=True, timeout=15,
    )
    if ssh_meta.returncode != 0:
        click.secho(f"  Failed to write metadata: {ssh_meta.stderr.strip()}", fg="red")
        return

    click.secho(f"  Requested: {header.title}", fg="green")
    click.echo(f"  Host: {target}")
    click.echo(f"  ID: {task_id}")

    # Auto-notify Matt about the new request
    desc_preview = (header.description or "").split("\n")[0][:80]
    msg = f"{header.title}"
    if desc_preview:
        msg += f" - {desc_preview}"
    _send_notification(config, target, "Brotherly: New Request", msg, has_pending=True)


@main.command()
@click.argument("message")
@click.option("--title", "-t", default="Brotherly", help="Notification title")
@click.option("--host", "-h", default=None, help="Remote host (SSH config alias)")
@click.option("--pending", is_flag=True, help="Mark as having pending requests (clickable)")
def notify(message: str, title: str, host: str | None, pending: bool) -> None:
    """Send a notification to Matt."""
    config = Config.load()
    target = host or config.default_host

    if not target:
        click.secho("  No host configured. Use --host or set default_host.", fg="red")
        return

    _send_notification(config, target, title, message, pending)


def _send_notification(config, target, title, message, has_pending):
    """Write a notification JSON to the remote host."""
    import time

    notif_data = json.dumps({
        "title": title,
        "message": message,
        "has_pending_requests": has_pending,
        "sent_at": datetime.now().isoformat(),
    })

    remote_dir = config.remote_data_dir + "/notifications"
    filename = f"{int(time.time() * 1000)}.json"

    ssh_mkdir = subprocess.run(
        ["ssh", target, f"mkdir -p {remote_dir}"],
        capture_output=True, text=True, timeout=15,
    )
    if ssh_mkdir.returncode != 0:
        click.secho(f"  Failed to create remote dir: {ssh_mkdir.stderr.strip()}", fg="red")
        return

    ssh_write = subprocess.run(
        ["ssh", target, f"cat > {remote_dir}/{filename}"],
        input=notif_data, capture_output=True, text=True, timeout=15,
    )
    if ssh_write.returncode != 0:
        click.secho(f"  Failed to send notification: {ssh_write.stderr.strip()}", fg="red")
        return

    click.secho(f"  Sent: {message}", fg="green")


@main.command(name="list")
@click.option("--all", "show_all", is_flag=True, help="Show all requests, not just pending")
def list_tasks(show_all: bool) -> None:
    """List requests."""
    config = Config.load()
    mgr = RequestManager(config)
    tasks = mgr.list_all() if show_all else mgr.list_pending()

    if not tasks:
        click.echo("No pending requests.")
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
        if task.description:
            click.echo(f"             {task.description.splitlines()[0][:60]}")
