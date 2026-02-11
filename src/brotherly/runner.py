"""Script execution with real-time output capture."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from brotherly.config import Config
from brotherly.models import QueuedTask, TaskStatus
from brotherly.queue import QueueManager


async def run_script(
    task: QueuedTask,
    queue: QueueManager,
    config: Config,
    on_output: Callable[[str], None] | None = None,
) -> int:
    """Execute a queued script with live output capture.

    Returns the exit code.
    """
    script_path = queue.get_script_path(task)
    log_path = queue.log_path(task)

    # Mark as running
    task.status = TaskStatus.RUNNING
    queue.update_task(task)

    with open(log_path, "w") as log_file:
        log_file.write(f"=== Brotherly Task: {task.title} ===\n")
        log_file.write(f"Script: {task.script_filename}\n")
        log_file.write(f"Started: {datetime.now().isoformat()}\n")
        log_file.write(f"{'=' * 50}\n\n")

        try:
            process = await asyncio.create_subprocess_exec(
                "/bin/bash",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                log_file.write(text)
                log_file.flush()
                if on_output:
                    on_output(text.rstrip("\n"))

            await process.wait()
            exit_code = process.returncode

        except Exception as exc:
            error_msg = f"\n[ERROR] {exc}\n"
            log_file.write(error_msg)
            if on_output:
                on_output(error_msg.strip())
            exit_code = 1

        log_file.write(f"\n{'=' * 50}\n")
        log_file.write(f"Finished: {datetime.now().isoformat()}\n")
        log_file.write(f"Exit code: {exit_code}\n")

    # Update task status
    task.exit_code = exit_code
    task.completed_at = datetime.now().isoformat()
    task.status = TaskStatus.COMPLETED if exit_code == 0 else TaskStatus.FAILED
    queue.update_task(task)

    return exit_code
