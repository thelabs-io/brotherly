#!/usr/bin/env python3
"""Brotherly request watcher - macOS notification handler.

Triggered by a LaunchAgent when new files appear in the requests
directory. Shows native macOS dialogs for each pending request and
handles approval, execution, and notification.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def find_requests_dir():
    """Find the brotherly requests directory."""
    candidates = [
        Path.home() / "Bros" / "Projects" / "brotherly" / "requests",
        Path.home() / ".brotherly" / "requests",
    ]
    for d in candidates:
        if d.is_dir():
            return d
    return None


def find_logs_dir():
    """Find or create the logs directory."""
    candidates = [
        Path.home() / "Bros" / "Projects" / "brotherly" / "logs",
        Path.home() / ".brotherly" / "logs",
    ]
    for d in candidates:
        if d.is_dir():
            return d
    logs = candidates[0]
    logs.mkdir(parents=True, exist_ok=True)
    return logs


def get_unnotified_pending_tasks(requests_dir):
    """Return list of (json_path, task_data) for pending requests not yet notified."""
    pending = []
    for f in sorted(requests_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            if data.get("status") == "pending" and not data.get("notified_at"):
                pending.append((f, data))
        except (json.JSONDecodeError, KeyError):
            continue
    return pending


def mark_notified(json_path, task_data):
    """Stamp the task so the watcher won't re-notify for it."""
    task_data["notified_at"] = datetime.now().isoformat()
    json_path.write_text(json.dumps(task_data, indent=2))


def osascript_dialog(title, message, buttons, default_button=None, icon="note"):
    """Show a macOS dialog via osascript. Returns the button clicked."""
    buttons_str = ", ".join(f'"{b}"' for b in buttons)
    default = f' default button "{default_button}"' if default_button else ""
    script = (
        f'display dialog "{message}" '
        f"buttons {{{buttons_str}}}{default} "
        f'with title "{title}" with icon {icon}'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            return None
        # Output is like "button returned:Approve"
        return result.stdout.strip().split(":")[-1]
    except (subprocess.TimeoutExpired, Exception):
        return None


def osascript_notify(title, message):
    """Show a macOS notification center alert."""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def show_script(script_path):
    """Open the script in the default text editor."""
    subprocess.Popen(["open", "-t", str(script_path)])


def run_script(script_path, log_path, requires_sudo=False):
    """Execute a script and capture output. Returns exit code."""
    if requires_sudo:
        escaped = str(script_path).replace("\\", "\\\\").replace('"', '\\"')
        script = (
            f'do shell script "bash \\"{escaped}\\" 2>&1" '
            f"with administrator privileges"
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=600,
            )
            log_path.write_text(result.stdout + result.stderr)
            return result.returncode
        except subprocess.TimeoutExpired:
            log_path.write_text("ERROR: Script timed out after 10 minutes")
            return 1
        except Exception as e:
            log_path.write_text(f"ERROR: {e}")
            return 1
    else:
        try:
            with open(log_path, "w") as log_file:
                result = subprocess.run(
                    ["bash", str(script_path)],
                    stdout=log_file, stderr=subprocess.STDOUT,
                    timeout=600,
                )
            return result.returncode
        except subprocess.TimeoutExpired:
            with open(log_path, "a") as f:
                f.write("\nERROR: Script timed out after 10 minutes")
            return 1
        except Exception as e:
            with open(log_path, "a") as f:
                f.write(f"\nERROR: {e}")
            return 1


def update_task(json_path, task_data, exit_code):
    """Update task status in the JSON file."""
    task_data["exit_code"] = exit_code
    task_data["completed_at"] = datetime.now().isoformat()
    task_data["status"] = "completed" if exit_code == 0 else "failed"
    json_path.write_text(json.dumps(task_data, indent=2))


def notify_chris(task_id, log_path):
    """Send notification to Chris via the brotherly notify_cmd."""
    brotherly_dir = Path.home() / "Bros" / "Projects" / "brotherly"
    try:
        subprocess.Popen(
            [sys.executable, "-m", "brotherly.notify_cmd", task_id, str(log_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(brotherly_dir),
        )
    except Exception:
        pass


def run_verification(executed_tasks, logs_dir):
    """Run Claude verification on executed tasks."""
    if not executed_tasks:
        return

    claude_path = subprocess.run(
        ["which", "claude"], capture_output=True, text=True
    )
    if claude_path.returncode != 0:
        return

    summary_lines = []
    for task_data, log_path in executed_tasks:
        ec = task_data.get("exit_code", "?")
        status = "OK" if ec == 0 else f"FAILED (exit {ec})"
        summary_lines.append(f"- [{status}] {task_data['title']}")
        if task_data.get("description"):
            summary_lines.append(f"  Description: {task_data['description']}")
        summary_lines.append(f"  Log: {log_path}")
        summary_lines.append("")

    summary = "\n".join(summary_lines)
    prompt = (
        "You are a post-install verification agent on Matt's Mac Mini.\n\n"
        "The following brotherly requests were just executed by Matt:\n\n"
        f"{summary}\n"
        "Your job:\n"
        "1. Read the log files to understand what happened.\n"
        "2. Verify each task actually succeeded - check that the expected "
        "files, commands, or configs exist and work.\n"
        "3. If anything failed or is broken, fix it.\n"
        "4. Report what you verified and what you fixed (if anything).\n\n"
        "Be thorough but concise."
    )

    try:
        subprocess.run(
            ["claude", "--dangerously-skip-permissions", "-p", prompt],
            cwd=str(Path.home()),
            timeout=300,
        )
    except Exception:
        pass


def main():
    requests_dir = find_requests_dir()
    if not requests_dir:
        return

    pending = get_unnotified_pending_tasks(requests_dir)
    if not pending:
        return

    logs_dir = find_logs_dir()

    # Mark all tasks as notified immediately, before any dialogs.
    # This prevents re-triggers: even if the watcher fires again
    # while a dialog is open, it won't find unnotified tasks.
    for json_path, task_data in pending:
        mark_notified(json_path, task_data)

    count = len(pending)
    osascript_notify(
        "Brotherly",
        f"{count} new request{'s' if count > 1 else ''} from Chris",
    )

    executed_tasks = []

    for json_path, task_data in pending:
        title = task_data.get("title", "Unknown")
        desc = task_data.get("description", "No description")
        requires_sudo = task_data.get("requires_sudo", False)
        task_id = task_data.get("id", json_path.stem)

        desc_display = desc[:500].replace('"', '\\"').replace("\n", "\\n")
        sudo_note = "\\n\\n(requires admin password)" if requires_sudo else ""

        msg = f"{desc_display}{sudo_note}"

        while True:
            choice = osascript_dialog(
                f"Brotherly: {title}",
                msg,
                ["Skip", "View Script", "Approve"],
                default_button="Approve",
            )

            if choice == "View Script":
                script_name = task_data.get("script_filename", f"{task_id}.sh")
                script_path = requests_dir / script_name
                if script_path.exists():
                    show_script(script_path)
                continue

            break

        if choice == "Approve":
            script_name = task_data.get("script_filename", f"{task_id}.sh")
            script_path = requests_dir / script_name
            log_path = logs_dir / f"{task_id}.log"

            task_data["status"] = "running"
            json_path.write_text(json.dumps(task_data, indent=2))

            exit_code = run_script(script_path, log_path, requires_sudo)
            update_task(json_path, task_data, exit_code)
            executed_tasks.append((task_data, log_path))

            if exit_code == 0:
                osascript_notify("Brotherly", f"Completed: {title}")
            else:
                osascript_notify("Brotherly", f"Failed: {title} (exit {exit_code})")

            notify_chris(task_id, log_path)

        elif choice is None:
            break

    if executed_tasks:
        run_verification(executed_tasks, logs_dir)


if __name__ == "__main__":
    main()
