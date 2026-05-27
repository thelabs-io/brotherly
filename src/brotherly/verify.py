"""Post-execution verification via Claude CLI."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from brotherly.config import Config
from brotherly.models import QueuedTask


def verify_batch(tasks: list[QueuedTask], config: Config) -> None:
    """Invoke claude to verify a batch of completed tasks."""
    if not tasks:
        return

    if not _claude_available():
        print("\n\033[2m  Skipping verification: claude CLI not found.\033[0m")
        return

    summary_lines = []
    log_paths = []
    for task in tasks:
        status = "OK" if task.exit_code == 0 else f"FAILED (exit {task.exit_code})"
        summary_lines.append(f"- [{status}] {task.title}")
        if task.description:
            summary_lines.append(f"  Description: {task.description}")
        log_path = config.logs_dir / f"{task.id}.log"
        if log_path.exists():
            summary_lines.append(f"  Log: {log_path}")
            log_paths.append(str(log_path))
        summary_lines.append("")

    summary = "\n".join(summary_lines)

    prompt = f"""You are a post-install verification agent on Matt's Mac Mini.

The following brotherly requests were just executed by Matt:

{summary}

Your job:
1. Read the log files to understand what happened.
2. Verify each task actually succeeded - check that the expected files, commands, or configs exist and work.
3. If anything failed or is broken, fix it. You have full access to the system.
4. Report what you verified and what you fixed (if anything).

Be thorough but concise. Focus on functional verification - can the tools actually run?"""

    print(f"\n\033[1;36m{'═' * 60}\033[0m")
    print(f"\033[1;36m  Verifying {len(tasks)} completed request(s) with Claude...\033[0m")
    print(f"\033[1;36m{'═' * 60}\033[0m\n")

    try:
        subprocess.call(
            ["claude", "--dangerously-skip-permissions", "-p", prompt],
            cwd=str(Path.home()),
        )
    except Exception as e:
        print(f"\n\033[33m  Verification error: {e}\033[0m")

    print(f"\n\033[1;36m{'═' * 60}\033[0m")
    print(f"\033[1;36m  Verification complete.\033[0m")
    print(f"\033[1;36m{'═' * 60}\033[0m\n")


def _claude_available() -> bool:
    try:
        result = subprocess.run(
            ["which", "claude"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False
