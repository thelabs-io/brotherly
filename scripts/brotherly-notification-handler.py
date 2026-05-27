#!/usr/bin/env python3
"""Brotherly notification handler - shows macOS notifications for Matt.

Triggered by a LaunchAgent when new files appear in the notifications
directory. Uses terminal-notifier for clickable notifications that
open the brotherly TUI in Terminal.app.

Falls back to osascript if terminal-notifier is not installed.
"""

import json
import subprocess
import shutil
from pathlib import Path

NOTIFICATIONS_DIR = Path.home() / "Bros" / "Projects" / "brotherly" / "notifications"
BROTHERLY_DIR = Path.home() / "Bros" / "Projects" / "brotherly"


def show_notification(title, message, has_pending_requests=False):
    """Show a macOS notification. Clickable if terminal-notifier is available."""
    tn = shutil.which("terminal-notifier")
    if not tn:
        tn_brew = Path("/opt/homebrew/bin/terminal-notifier")
        if tn_brew.exists():
            tn = str(tn_brew)

    if tn:
        cmd = [
            tn,
            "-title", title,
            "-message", message,
            "-sender", "com.apple.Terminal",
            "-sound", "default",
            "-group", "brotherly",
        ]
        if has_pending_requests:
            cmd.extend([
                "-execute",
                f'/usr/bin/open -a Terminal.app "{BROTHERLY_DIR}/scripts/open-brotherly.sh"',
            ])
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception:
            _fallback_notification(title, message)
    else:
        _fallback_notification(title, message)


def _fallback_notification(title, message):
    """Fallback to osascript (no click action)."""
    message_escaped = message.replace('"', '\\"')
    title_escaped = title.replace('"', '\\"')
    script = f'display notification "{message_escaped}" with title "{title_escaped}" sound name "default"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except Exception:
        pass


def process_notifications():
    """Process and remove notification files."""
    if not NOTIFICATIONS_DIR.is_dir():
        return

    for f in sorted(NOTIFICATIONS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            title = data.get("title", "Brotherly")
            message = data.get("message", "")
            has_pending = data.get("has_pending_requests", False)

            if message:
                show_notification(title, message, has_pending)

            try:
                f.unlink()
            except OSError:
                pass
        except (json.JSONDecodeError, Exception):
            try:
                f.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    process_notifications()
