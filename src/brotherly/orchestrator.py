"""Main orchestration loop: TUI review → shell execution → TUI summary → notify.

The key design principle: the TUI never executes scripts. It only handles
review and display. Script execution happens in the raw terminal with a real
TTY, so sudo prompts, interactive commands, and TTY-dependent tools all work.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from datetime import datetime

from brotherly.config import Config
from brotherly.models import TaskStatus
from brotherly.request import RequestManager


def run(config: Config | None = None) -> None:
    """Main entry point — the loop Matt interacts with."""
    if config is None:
        config = Config.load()
    requests = RequestManager(config)
    executed_tasks: list = []

    while True:
        pending = requests.list_pending()
        if not pending:
            _print_no_requests()
            break

        # Phase 1: TUI review — Matt picks a request and runs/skips/quits
        from brotherly.app import ReviewApp

        app = ReviewApp(config=config, request_manager=requests)
        app.run()
        decision = app.result

        if decision is None or decision.get("action") == "quit":
            break

        if decision.get("action") == "skip":
            continue

        if decision.get("action") != "run":
            break

        task_id = decision["task_id"]
        task = requests.get_task(task_id)
        if task is None:
            continue

        # Phase 2: Execute script in the real terminal
        script_path = requests.get_script_path(task)
        log_path = requests.log_path(task)
        config.ensure_dirs()

        task.status = TaskStatus.RUNNING
        requests.update_task(task)

        print(f"\n\033[1;34m{'═' * 60}\033[0m")
        print(f"\033[1m  Executing: {task.title}\033[0m")
        if task.requires_sudo:
            print(f"\033[1;33m  ⚠ This script requires sudo\033[0m")
        print(f"\033[1;34m{'═' * 60}\033[0m\n")

        # Run with real TTY via subprocess.call (no PIPE = inherited terminal)
        # Use bash pipefail so we get the script's exit code, not tee's
        # cwd=data_dir so scripts don't depend on where brotherly was launched
        exit_code = subprocess.call(
            f'set -o pipefail; bash {shlex.quote(str(script_path))} 2>&1 | tee {shlex.quote(str(log_path))}',
            shell=True,
            executable="/bin/bash",
            cwd=str(config.data_dir),
        )

        # Update task status
        task.exit_code = exit_code
        task.completed_at = datetime.now().isoformat()
        task.status = TaskStatus.COMPLETED if exit_code == 0 else TaskStatus.FAILED
        requests.update_task(task)
        executed_tasks.append(task)

        success = exit_code == 0
        if success:
            print(f"\n\033[1;32m{'═' * 60}\033[0m")
            print(f"\033[1;32m  ✓ Completed successfully\033[0m")
            print(f"\033[1;32m{'═' * 60}\033[0m\n")
        else:
            print(f"\n\033[1;31m{'═' * 60}\033[0m")
            print(f"\033[1;31m  ✗ Failed (exit code {exit_code})\033[0m")
            print(f"\033[1;31m{'═' * 60}\033[0m\n")

        # Phase 3: TUI summary
        from brotherly.app import SummaryApp

        summary = SummaryApp(task=task, log_path=log_path)
        summary.run()

        # Phase 4: Send notifications in background
        _notify_background(task_id, str(log_path))

    # Phase 5: Verify all executed tasks with Claude
    if executed_tasks:
        try:
            from brotherly.verify import verify_batch

            verify_batch(executed_tasks, config)
        except Exception as e:
            print(f"\n\033[33m  Verification skipped: {e}\033[0m")


def _print_no_requests() -> None:
    print("\033[2m  No pending requests.\033[0m")
    print("\033[2m  When Chris sends a request, run brotherly again.\033[0m")


def _notify_background(task_id: str, log_path: str) -> None:
    """Spawn notification in a background process."""
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "brotherly.notify_cmd",
            task_id,
            log_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
