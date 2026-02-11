"""Queue management for brotherly tasks."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from brotherly.config import Config
from brotherly.models import QueuedTask, TaskStatus


class QueueManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.config.ensure_dirs()

    def add_task(
        self,
        script_path: Path,
        title: str,
        description: str,
        requires_sudo: bool = False,
    ) -> QueuedTask:
        task_id = QueuedTask.generate_id(title)
        script_filename = f"{task_id}.sh"

        # Copy script to queue directory
        dest = self.config.queue_dir / script_filename
        shutil.copy2(script_path, dest)
        dest.chmod(0o755)

        task = QueuedTask(
            id=task_id,
            script_filename=script_filename,
            title=title,
            description=description,
            queued_at=datetime.now().isoformat(),
            requires_sudo=requires_sudo,
        )

        # Write metadata
        meta_path = self.config.queue_dir / f"{task_id}.json"
        meta_path.write_text(task.to_json())

        return task

    def list_pending(self) -> list[QueuedTask]:
        tasks = []
        for json_file in sorted(self.config.queue_dir.glob("*.json")):
            task = QueuedTask.from_file(json_file)
            if task.status == TaskStatus.PENDING:
                tasks.append(task)
        return tasks

    def list_all(self) -> list[QueuedTask]:
        tasks = []
        for json_file in sorted(self.config.queue_dir.glob("*.json")):
            tasks.append(QueuedTask.from_file(json_file))
        return tasks

    def get_task(self, task_id: str) -> QueuedTask | None:
        meta_path = self.config.queue_dir / f"{task_id}.json"
        if not meta_path.exists():
            return None
        return QueuedTask.from_file(meta_path)

    def get_script_content(self, task: QueuedTask) -> str:
        script_path = self.config.queue_dir / task.script_filename
        return script_path.read_text()

    def get_script_path(self, task: QueuedTask) -> Path:
        return self.config.queue_dir / task.script_filename

    def update_task(self, task: QueuedTask) -> None:
        meta_path = self.config.queue_dir / f"{task.id}.json"
        meta_path.write_text(task.to_json())

    def log_path(self, task: QueuedTask) -> Path:
        return self.config.logs_dir / f"{task.id}.log"
