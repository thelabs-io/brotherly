"""Tests for script header parser."""

import tempfile
from pathlib import Path

import pytest

from brotherly.script_parser import ScriptHeader, parse_script_header


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _write_script(tmp_dir: Path, name: str, content: str) -> Path:
    p = tmp_dir / name
    p.write_text(content)
    return p


def test_full_header(tmp_dir):
    path = _write_script(tmp_dir, "install.sh", """\
#!/bin/bash
# Install Homebrew
#
# This installs the **Homebrew** package manager.
#
# It will:
# - Download the installer
# - Run the installation

set -euo pipefail
echo "installing"
""")
    header = parse_script_header(path)
    assert header.title == "Install Homebrew"
    assert "**Homebrew**" in header.description
    assert "- Download the installer" in header.description
    assert "- Run the installation" in header.description
    assert header.body_start_line == 9


def test_title_only(tmp_dir):
    path = _write_script(tmp_dir, "fix.sh", """\
#!/bin/bash
# Fix DNS settings

echo "fixing"
""")
    header = parse_script_header(path)
    assert header.title == "Fix DNS settings"
    assert header.description == ""
    assert header.body_start_line == 3


def test_no_header(tmp_dir):
    path = _write_script(tmp_dir, "raw-script.sh", """\
#!/bin/bash
set -e
echo "hello"
""")
    header = parse_script_header(path)
    assert header.title == "raw-script"
    assert header.description == ""


def test_no_shebang(tmp_dir):
    path = _write_script(tmp_dir, "simple.sh", """\
# Update system
#
# Runs apt update and upgrade.

apt update && apt upgrade -y
""")
    header = parse_script_header(path)
    assert header.title == "Update system"
    assert "apt update and upgrade" in header.description


def test_explicit_delimiter(tmp_dir):
    path = _write_script(tmp_dir, "tricky.sh", """\
#!/bin/bash
# Configure networking
#
# Sets up static IP and DNS.
# ---
# shellcheck disable=SC2034
IFACE="eth0"
""")
    header = parse_script_header(path)
    assert header.title == "Configure networking"
    assert "static IP" in header.description
    # shellcheck line should NOT be in description
    assert "shellcheck" not in header.description
    # body should start at the shellcheck line
    assert header.body_start_line == 5


def test_blank_comment_lines_preserved(tmp_dir):
    path = _write_script(tmp_dir, "multi.sh", """\
#!/bin/bash
# Deploy app
#
# Step 1: Pull latest code.
#
# Step 2: Restart services.

systemctl restart app
""")
    header = parse_script_header(path)
    assert header.title == "Deploy app"
    lines = header.description.split("\n")
    assert "Step 1: Pull latest code." in lines
    assert "" in lines  # blank line preserved between steps
    assert "Step 2: Restart services." in lines


def test_markdown_formatting(tmp_dir):
    path = _write_script(tmp_dir, "fancy.sh", """\
#!/bin/bash
# Install dependencies
#
# This script installs:
#
# 1. **Node.js** via `nvm`
# 2. [Rust](https://rustup.rs/)
# 3. `python3-venv`
#
# > Warning: requires internet connection

curl -o- https://example.com/install.sh | bash
""")
    header = parse_script_header(path)
    assert header.title == "Install dependencies"
    assert "**Node.js**" in header.description
    assert "[Rust](https://rustup.rs/)" in header.description
    assert "> Warning:" in header.description


def test_empty_file(tmp_dir):
    path = _write_script(tmp_dir, "empty.sh", "")
    header = parse_script_header(path)
    assert header.title == "empty"
    assert header.description == ""


def test_shebang_only(tmp_dir):
    path = _write_script(tmp_dir, "bare.sh", "#!/bin/bash\n")
    header = parse_script_header(path)
    assert header.title == "bare"
    assert header.description == ""
