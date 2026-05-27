#!/bin/bash
# Update Coderoo
#
# Pulls the latest Coderoo source and ensures it is installed as an
# editable uv tool for Matt's account.
#
# If Coderoo is already installed via `uv tool install -e`, this just
# runs `git pull` - the editable install picks up changes automatically.
#
# If it is not installed yet, installs it with `uv tool install -e .`
# so that future updates only need a `git pull`.
#
# Repo location: `~/Bros/Projects/coderoo`
# ---

set -euo pipefail

CODEROO_DIR="$HOME/Bros/Projects/coderoo"

if [[ ! -d "$CODEROO_DIR" ]]; then
    echo "Error: Coderoo repo not found at $CODEROO_DIR"
    exit 1
fi

cd "$CODEROO_DIR"

echo "Pulling latest Coderoo..."
git pull
echo ""

if uv tool list 2>/dev/null | grep -q coderoo; then
    echo "Coderoo is already installed as a uv tool (editable)."
    echo "git pull is sufficient - changes are picked up automatically."
else
    echo "Coderoo is not installed as a uv tool. Installing..."
    uv tool install -e .
    echo ""
    echo "Installed! Verify with:"
    echo "  coderoo --help"
fi

echo ""
echo "=== Status ==="
echo "Repo: $CODEROO_DIR"
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git log --oneline -1)"
if command -v coderoo &>/dev/null; then
    echo "CLI: $(which coderoo)"
else
    echo "CLI: not in PATH (may need to restart shell)"
fi
