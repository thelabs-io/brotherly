"""Tests for request management."""

import tempfile
from pathlib import Path

import pytest

from brotherly.config import Config
from brotherly.models import TaskStatus
from brotherly.request import RequestManager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def config(temp_dir):
    return Config(data_dir=temp_dir)


@pytest.fixture
def mgr(config):
    return RequestManager(config)


@pytest.fixture
def sample_script(temp_dir):
    script = temp_dir / "test.sh"
    script.write_text("#!/bin/bash\n# Hello World\n#\n# A test script that prints hello world.\n\necho 'hello world'\n")
    return script


def test_add_task(mgr, sample_script):
    task = mgr.add_task(sample_script)
    assert task.title == "Hello World"
    assert task.description == "A test script that prints hello world."
    assert task.status == TaskStatus.PENDING
    assert (mgr.config.requests_dir / f"{task.id}.json").exists()
    assert (mgr.config.requests_dir / task.script_filename).exists()


def test_list_pending(mgr, temp_dir):
    s1 = temp_dir / "s1.sh"
    s1.write_text("#!/bin/bash\n# Task 1\n#\n# First task\n\necho 1\n")
    s2 = temp_dir / "s2.sh"
    s2.write_text("#!/bin/bash\n# Task 2\n#\n# Second task\n\necho 2\n")

    mgr.add_task(s1)
    mgr.add_task(s2)

    tasks = mgr.list_pending()
    assert len(tasks) == 2
    assert tasks[0].title == "Task 1"
    assert tasks[1].title == "Task 2"


def test_get_task(mgr, sample_script):
    added = mgr.add_task(sample_script)
    found = mgr.get_task(added.id)
    assert found is not None
    assert found.title == "Hello World"


def test_get_task_not_found(mgr):
    assert mgr.get_task("nonexistent") is None


def test_update_task(mgr, sample_script):
    task = mgr.add_task(sample_script)
    task.status = TaskStatus.COMPLETED
    task.exit_code = 0
    mgr.update_task(task)

    reloaded = mgr.get_task(task.id)
    assert reloaded.status == TaskStatus.COMPLETED
    assert reloaded.exit_code == 0


def test_get_script_content(mgr, sample_script):
    task = mgr.add_task(sample_script)
    content = mgr.get_script_content(task)
    assert "echo 'hello world'" in content


def test_list_pending_excludes_completed(mgr, temp_dir):
    s1 = temp_dir / "done.sh"
    s1.write_text("#!/bin/bash\n# Done Task\n#\n# Already done\n\necho done\n")
    s2 = temp_dir / "pending.sh"
    s2.write_text("#!/bin/bash\n# Pending Task\n#\n# Still pending\n\necho pending\n")

    task = mgr.add_task(s1)
    task.status = TaskStatus.COMPLETED
    mgr.update_task(task)

    mgr.add_task(s2)

    pending = mgr.list_pending()
    assert len(pending) == 1
    assert pending[0].title == "Pending Task"
