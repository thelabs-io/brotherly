"""Tests for queue management."""

import tempfile
from pathlib import Path

import pytest

from brotherly.config import Config
from brotherly.models import TaskStatus
from brotherly.queue import QueueManager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def config(temp_dir):
    return Config(data_dir=temp_dir)


@pytest.fixture
def queue(config):
    return QueueManager(config)


@pytest.fixture
def sample_script(temp_dir):
    script = temp_dir / "test.sh"
    script.write_text("#!/bin/bash\necho 'hello world'\n")
    return script


def test_add_task(queue, sample_script):
    task = queue.add_task(
        sample_script,
        title="Test Script",
        description="A test script that prints hello world.",
    )
    assert task.title == "Test Script"
    assert task.status == TaskStatus.PENDING
    assert (queue.config.queue_dir / f"{task.id}.json").exists()
    assert (queue.config.queue_dir / task.script_filename).exists()


def test_list_pending(queue, sample_script):
    queue.add_task(sample_script, "Task 1", "First task")
    queue.add_task(sample_script, "Task 2", "Second task")

    tasks = queue.list_pending()
    assert len(tasks) == 2
    assert tasks[0].title == "Task 1"
    assert tasks[1].title == "Task 2"


def test_get_task(queue, sample_script):
    added = queue.add_task(sample_script, "Find Me", "A findable task")
    found = queue.get_task(added.id)
    assert found is not None
    assert found.title == "Find Me"


def test_get_task_not_found(queue):
    assert queue.get_task("nonexistent") is None


def test_update_task(queue, sample_script):
    task = queue.add_task(sample_script, "Update Me", "Will be updated")
    task.status = TaskStatus.COMPLETED
    task.exit_code = 0
    queue.update_task(task)

    reloaded = queue.get_task(task.id)
    assert reloaded.status == TaskStatus.COMPLETED
    assert reloaded.exit_code == 0


def test_get_script_content(queue, sample_script):
    task = queue.add_task(sample_script, "Read Source", "Read the script")
    content = queue.get_script_content(task)
    assert "echo 'hello world'" in content


def test_list_pending_excludes_completed(queue, sample_script):
    task = queue.add_task(sample_script, "Done Task", "Already done")
    task.status = TaskStatus.COMPLETED
    queue.update_task(task)

    queue.add_task(sample_script, "Pending Task", "Still pending")

    pending = queue.list_pending()
    assert len(pending) == 1
    assert pending[0].title == "Pending Task"
