"""Notification system - SSH to z2 for SMS and GNOME notifications."""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path

from brotherly.config import Config
from brotherly.models import QueuedTask


async def notify_chris(
    task: QueuedTask,
    log_path: Path,
    config: Config,
    on_status: callable | None = None,
) -> bool:
    """Send notifications to Chris on z2. Returns True if all succeeded."""
    ssh_target = f"{config.z2_user}@{config.z2_host}"
    ssh_base = ["ssh", "-p", str(config.z2_port), "-o", "ConnectTimeout=10", ssh_target]

    success = task.exit_code == 0
    status_emoji = "+" if success else "FAIL"
    status_word = "completed successfully" if success else f"FAILED (exit {task.exit_code})"
    sms_msg = f"Brotherly [{status_emoji}]: {task.title} {status_word}"

    all_ok = True

    # Step 1: SCP log file to z2
    if on_status:
        on_status("Copying log to z2...")
    try:
        scp_dest = f"{ssh_target}:{config.z2_log_dir}/{log_path.name}"
        # Ensure remote log directory exists
        mkdir_proc = await asyncio.create_subprocess_exec(
            *ssh_base, f"mkdir -p {shlex.quote(config.z2_log_dir)}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await mkdir_proc.wait()

        scp_proc = await asyncio.create_subprocess_exec(
            "scp", "-P", str(config.z2_port), "-o", "ConnectTimeout=10",
            str(log_path), scp_dest,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await scp_proc.communicate()
        if scp_proc.returncode != 0:
            all_ok = False
    except Exception:
        all_ok = False

    # Step 2: Send SMS
    if on_status:
        on_status("Sending SMS...")
    try:
        sms_cmd = f"send-sms {shlex.quote(config.phone_number)} {shlex.quote(sms_msg)}"
        sms_proc = await asyncio.create_subprocess_exec(
            *ssh_base, sms_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await sms_proc.communicate()
        if sms_proc.returncode != 0:
            all_ok = False
    except Exception:
        all_ok = False

    # Step 3: GNOME notification with click-to-open-log
    if on_status:
        on_status("Sending desktop notification...")
    try:
        urgency = "normal" if success else "critical"
        icon = "dialog-information" if success else "dialog-error"
        remote_log = f"{config.z2_log_dir}/{log_path.name}"

        # Use notify-send with --action; backgrounded so it doesn't block SSH
        notify_script = (
            f'DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus '
            f'nohup bash -c \''
            f'ACTION=$(notify-send '
            f'--urgency={urgency} '
            f'--app-name=Brotherly '
            f'--icon={icon} '
            f'"Brotherly: {task.title}" '
            f'{shlex.quote(status_word)} '
            f'--action=view=View\\ Log '
            f'--wait 2>/dev/null); '
            f'if [ "$ACTION" = "view" ]; then '
            f'xdg-open {shlex.quote(remote_log)}; '
            f'fi\' &>/dev/null &'
        )
        notify_proc = await asyncio.create_subprocess_exec(
            *ssh_base, notify_script,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await notify_proc.wait()
    except Exception:
        all_ok = False

    if on_status:
        on_status("Notifications sent!" if all_ok else "Some notifications failed")

    return all_ok
