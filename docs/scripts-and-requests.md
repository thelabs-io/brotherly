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

1. The script header is parsed for title/description
2. The script and metadata JSON are copied to the remote host via SSH/SCP
3. The request appears in Matt's TUI when he runs `brotherly`
4. Matt can review the description, view source, and choose to run it

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
