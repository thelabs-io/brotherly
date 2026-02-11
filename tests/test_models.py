"""Tests for data models."""

import json

from brotherly.models import QueuedTask, TaskStatus


def test_generate_id():
    task_id = QueuedTask.generate_id("Install Homebrew")
    parts = task_id.split("-")
    # Should start with date-time prefix
    assert len(parts[0]) == 8  # YYYYMMDD
    assert len(parts[1]) == 6  # HHMMSS
    assert "install" in task_id
    assert "homebrew" in task_id


def test_roundtrip_json():
    task = QueuedTask(
        id="20260211-143022-install-homebrew",
        script_filename="20260211-143022-install-homebrew.sh",
        title="Install Homebrew",
        description="Installs the Homebrew package manager.",
        queued_at="2026-02-11T14:30:22",
        queued_by="chris",
        requires_sudo=True,
    )
    json_str = task.to_json()
    parsed = json.loads(json_str)
    assert parsed["status"] == "pending"
    assert parsed["requires_sudo"] is True

    restored = QueuedTask.from_json(json_str)
    assert restored.id == task.id
    assert restored.title == task.title
    assert restored.status == TaskStatus.PENDING
    assert restored.requires_sudo is True


def test_status_values():
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"
