"""Standalone notification command — called as a background process by the orchestrator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from brotherly.config import Config
from brotherly.notify import notify_chris
from brotherly.request import RequestManager


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m brotherly.notify_cmd <task_id> <log_path>", file=sys.stderr)
        sys.exit(1)

    task_id = sys.argv[1]
    log_path = Path(sys.argv[2])

    config = Config.load()
    requests = RequestManager(config)
    task = requests.get_task(task_id)

    if task is None:
        print(f"Task not found: {task_id}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(notify_chris(task, log_path, config))


if __name__ == "__main__":
    main()
