"""Notification system - SSH to z2 via restricted service key."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from brotherly.config import Config
from brotherly.models import QueuedTask


async def notify_chris(
    task: QueuedTask,
    log_path: Path,
    config: Config,
    on_status: callable | None = None,
) -> bool:
    """Send notifications to Chris on z2 via restricted service key.

    Single SSH call: metadata as command string, log piped via stdin.
    The server-side forced command handler does the rest.
    """
    if on_status:
        on_status("Sending notifications to z2...")

    # Base64-encode the title to safely pass spaces/special chars
    title_b64 = base64.b64encode(task.title.encode()).decode()
    exit_code = task.exit_code if task.exit_code is not None else 1

    # The "command" we send — the forced command handler reads SSH_ORIGINAL_COMMAND
    remote_cmd = f"notify {title_b64} status {exit_code}"

    ssh_key = str(Path(config.z2_ssh_key).expanduser())

    ssh_cmd = [
        "ssh",
        "-i", ssh_key,
        "-p", str(config.z2_port),
        "-o", "ConnectTimeout=10",
        "-o", "BatchMode=yes",
        f"{config.z2_user}@{config.z2_host}",
        remote_cmd,
    ]

    try:
        # Pipe log file contents via stdin
        stdin_data = b""
        if log_path.exists():
            stdin_data = log_path.read_bytes()

        proc = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=stdin_data)
        ok = proc.returncode == 0

        if on_status:
            on_status("Notifications sent!" if ok else "Notifications failed")
        return ok

    except Exception:
        if on_status:
            on_status("Notifications failed")
        return False
