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


# --- Prep command tests ---


def test_single_prep_line(tmp_dir):
    path = _write_script(tmp_dir, "install.sh", """\
#!/bin/bash
# Install tools
#
# Copies tools to Matt's account.
#
# prep: chmod -R g+rX ~/.local/share/tools/

rsync -av ~/.local/share/tools/ /Users/matt/tools/
""")
    header = parse_script_header(path)
    assert header.title == "Install tools"
    assert "Copies tools" in header.description
    assert "prep" not in header.description
    assert header.prep == "chmod -R g+rX ~/.local/share/tools/"


def test_multiple_prep_lines(tmp_dir):
    path = _write_script(tmp_dir, "stage.sh", """\
#!/bin/bash
# Stage files
#
# Stages files for deployment.
#
# prep: mkdir -p /tmp/staging
# prep: chmod -R g+rX ~/data/

cp -R /tmp/staging/ /Users/matt/deploy/
""")
    header = parse_script_header(path)
    assert header.title == "Stage files"
    assert "prep" not in header.description
    assert header.prep == "mkdir -p /tmp/staging\nchmod -R g+rX ~/data/"


def test_prep_block(tmp_dir):
    path = _write_script(tmp_dir, "deploy.sh", """\
#!/bin/bash
# Deploy application
#
# Full deployment with staging.
#
# prep-start
# mkdir -p /tmp/staging
# chmod -R g+rX ~/.config/app/
# cp -R ~/data /tmp/staging/
# prep-end

rsync -av /tmp/staging/ /Users/matt/app/
""")
    header = parse_script_header(path)
    assert header.title == "Deploy application"
    assert "Full deployment" in header.description
    assert "prep" not in header.description
    assert "mkdir -p /tmp/staging" in header.prep
    assert "chmod -R g+rX ~/.config/app/" in header.prep
    assert "cp -R ~/data /tmp/staging/" in header.prep


def test_prep_with_description_interleaved(tmp_dir):
    path = _write_script(tmp_dir, "mixed.sh", """\
#!/bin/bash
# Copy configs
#
# Copies config files to Matt's account.
# prep: chmod -R g+rX ~/.config/myapp/
#
# Safe to re-run.

cp -R ~/.config/myapp/ /Users/matt/.config/myapp/
""")
    header = parse_script_header(path)
    assert header.title == "Copy configs"
    assert "Copies config files" in header.description
    assert "Safe to re-run" in header.description
    assert "prep" not in header.description
    assert header.prep == "chmod -R g+rX ~/.config/myapp/"


def test_no_prep(tmp_dir):
    path = _write_script(tmp_dir, "simple.sh", """\
#!/bin/bash
# Simple task
#
# No prep needed.

echo "hello"
""")
    header = parse_script_header(path)
    assert header.prep == ""


def test_prep_with_delimiter(tmp_dir):
    path = _write_script(tmp_dir, "delim.sh", """\
#!/bin/bash
# Guarded script
#
# Has a setup step and a delimiter.
#
# prep: chmod g+r ~/secret.txt
# ---
# shellcheck disable=SC2034
VAR="value"
""")
    header = parse_script_header(path)
    assert header.title == "Guarded script"
    assert header.prep == "chmod g+r ~/secret.txt"
    assert "shellcheck" not in header.description
    assert "chmod" not in header.description
