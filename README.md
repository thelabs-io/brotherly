# Brotherly

A trust-based remote administration tool for brothers. Queue shell scripts for review and approval through a beautiful terminal UI.

## How It Works

1. **Chris** writes a script and queues it on Matt's machine via SSH
2. **Matt** runs `brotherly` and sees a description of what the script does
3. Matt can **view the source** if he's curious, then **approve** execution
4. The script runs with full output displayed in the TUI
5. Chris gets an **SMS and desktop notification** with the result

## Installation

### Prerequisites

- Python 3.11+
- uv or pipx

### Setup

```bash
# Install as a tool
uv tool install .

# Or install in development mode
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Usage

### Queue a script (Chris)

```bash
brotherly queue install-homebrew.sh \
    --title "Install Homebrew" \
    --description "Installs the Homebrew package manager for macOS"
```

### Review and run (Matt)

```bash
brotherly
```

## Development

See [docs/development.md](docs/development.md) for the development guide.

## Testing

```bash
pytest tests/ -v
```
