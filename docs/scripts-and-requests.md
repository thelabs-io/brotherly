# Writing Scripts & Sending Requests

## Script Format

Scripts use a comment header block for metadata. The first comment line is the **title**, and subsequent comment lines form the **description** (supports markdown).

```bash
#!/bin/bash
# Title goes here
#
# Description in **markdown** follows.
# Can span multiple lines.
#
# Supports:
# - Lists
# - `code`
# - [links](https://example.com)
# - **bold** and *italic*

set -euo pipefail
echo "actual code starts here"
```

### Header Rules

- **Shebang** (`#!`) is skipped automatically
- **First `#` line** after the shebang = title
- **Subsequent `#` lines** = description (markdown)
- **Blank `#` lines** (just `#`) become blank lines in the description
- **`# ---`** explicitly ends the header (useful when the next line is also a comment, like `# shellcheck disable=...`)
- **No header** = filename stem used as title, empty description
- The TUI "View Source" screen shows only the code body (header is stripped)

### Examples

Minimal (title only):
```bash
#!/bin/bash
# Update Homebrew packages

brew update && brew upgrade
```

With description:
```bash
#!/bin/bash
# Install development tools
#
# Sets up the standard dev environment:
#
# 1. Xcode command line tools
# 2. Homebrew
# 3. Node.js via nvm
#
# Safe to re-run — skips already-installed components.

set -euo pipefail
# ... installation code ...
```

With explicit delimiter (when code starts with comments):
```bash
#!/bin/bash
# Configure network settings
#
# Sets static IP and DNS for the home network.
# ---
# shellcheck disable=SC2034
IFACE="en0"
```

## Prep Commands

Scripts can include **prep commands** that run as the requester (chris) on the remote host *before* the request is queued for Matt. This is useful when the script needs files that chris owns to be group-readable, or when staging is required.

Prep commands are extracted from the header — they don't appear in the description shown in the TUI.

### Single-line prep

Use `# prep:` for one-off commands:

```bash
#!/bin/bash
# Install Claude Code agents
#
# Copies agents to Matt's config directory.
#
# prep: chmod -R g+rX ~/.claude/agents/

rsync -av /Users/chris/.claude/agents/ /Users/matt/.claude/agents/
```

Multiple `# prep:` lines run as a multi-line script:

```bash
# prep: mkdir -p /tmp/staging
# prep: chmod -R g+rX ~/data/
```

### Prep block

Use `# prep-start` / `# prep-end` for multi-line prep scripts:

```bash
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
```

### How it works

1. `brotherly request` parses the prep commands from the header
2. Before copying the script to the remote host, prep commands are executed via SSH as chris
3. If prep fails, the request is **not** queued (so Matt won't see a broken request)
4. If prep succeeds, the script and metadata are delivered normally

## Sending Requests

### Basic Usage

```bash
brotherly request path/to/script.sh
```

This reads the title and description from the script header and sends it to the configured default host.

### Options

```bash
# Send to a specific host (SSH config alias)
brotherly request script.sh --host matts-mini

# Mark as requiring sudo
brotherly request script.sh --sudo
```

### What Happens

1. The script header is parsed for title, description, and prep commands
2. If prep commands exist, they run as chris on the remote host
3. The script and metadata JSON are copied to the remote host via SSH/SCP
4. The request appears in Matt's TUI when he runs `brotherly`
5. Matt can review the description, view source, and choose to run it

### Configuration

The `default_host` setting in `~/.config/brotherly/config.json5` determines where requests go by default:

```json5
{
  "default_host": "matts-mini"
}
```

If no `--host` is given and no `default_host` is configured, the request is added locally.

### Listing Requests

```bash
# Show pending requests
brotherly list

# Show all requests (including completed/failed)
brotherly list --all
```
