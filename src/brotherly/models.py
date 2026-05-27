"""Data models for brotherly requests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueuedTask:
    id: str
    script_filename: str
    title: str
    description: str
    queued_at: str
    queued_by: str = "chris"
    status: TaskStatus = TaskStatus.PENDING
    requires_sudo: bool = False
    completed_at: str | None = None
    exit_code: int | None = None
    notified_at: str | None = None

    @staticmethod
    def generate_id(title: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = title.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")[:40]
        return f"{timestamp}-{slug}"

    def to_json(self) -> str:
        data = asdict(self)
        data["status"] = self.status.value
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, text: str) -> QueuedTask:
        data = json.loads(text)
        data["status"] = TaskStatus(data["status"])
        return cls(**data)

    @classmethod
    def from_file(cls, path: Path) -> QueuedTask:
        return cls.from_json(path.read_text())

    @property
    def age(self) -> str:
        queued = datetime.fromisoformat(self.queued_at)
        delta = datetime.now() - queued
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago" if minutes > 0 else "just now"
