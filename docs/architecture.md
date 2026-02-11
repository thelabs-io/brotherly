# Architecture

## System Overview

```
┌─────────────────────┐          SSH          ┌─────────────────────┐
│   z2 (Chris)        │ ──────────────────── │  matts-mini (Matt)  │
│                     │   brotherly queue     │                     │
│  Write scripts      │ ──────────────────→  │  ~/.brotherly/      │
│  Receive notifs     │                       │    queue/           │
│   - SMS (send-sms)  │   SSH notification    │    logs/            │
│   - GNOME notify    │ ←──────────────────  │    scripts/         │
│                     │                       │                     │
│                     │                       │  brotherly (TUI)    │
│                     │                       │    Review & approve │
└─────────────────────┘                       └─────────────────────┘
```

## Directory Layout (on Matt's machine)

```
/Users/matt/Bros/brotherly/
├── queue/              # Queued task metadata (JSON)
├── scripts/            # Actual script files
├── logs/               # Execution logs (accessible by Chris)
└── config.toml         # Configuration
```

## Queue Entry Format

Each queued task is a JSON file in `queue/`:

```json
{
    "id": "20260211-143022-install-homebrew",
    "script": "scripts/install-homebrew.sh",
    "title": "Install Homebrew",
    "description": "Installs Homebrew package manager...",
    "queued_at": "2026-02-11T14:30:22",
    "queued_by": "chris",
    "status": "pending",
    "requires_sudo": true
}
```

## Notification Flow

After script execution on Matt's machine:
1. Script output captured and logged
2. SSH connection to z2 (zara2stra.duckdns.org:22440)
3. Send SMS via `send-sms` on z2
4. Send GNOME notification via `notify-send` on z2
5. GNOME notification click opens the log file (via SSH/remote path)

## Components

- **CLI** (`cli.py`) - Command-line interface (queue, run, list)
- **TUI** (`app.py`) - Textual-based approval interface
- **Queue Manager** (`queue.py`) - Queue CRUD operations
- **Runner** (`runner.py`) - Script execution with output capture
- **Notifier** (`notify.py`) - SSH-based notification to z2
