# Development Guide

## Prerequisites

- Python 3.11+
- uv (package manager)

## Setup (on z2 for development)

```bash
cd /storage/Projects/brotherly
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Setup (on Matt's machine)

```bash
# Install via pipx or uv tool
pipx install /Users/matt/Bros/brotherly
# or
uv tool install /Users/matt/Bros/brotherly
```

## Running

```bash
# Launch TUI (Matt's workflow)
brotherly

# Queue a script (Chris's workflow, typically via SSH)
brotherly queue path/to/script.sh --title "Install Homebrew" --description "Installs Homebrew package manager"

# List queued tasks
brotherly list
```

## Testing

```bash
pytest tests/ -v
```
