#!/bin/bash
# Ensure cw (Claude wrapper) is on your PATH
#
# Checks that `~/Bros/Projects/scripts` is in your shell PATH so you
# can run `cw` from anywhere. If it's missing, adds it to your
# shell profile.
#
# `cw` is a wrapper around `claude` that adds:
# - **Self-restart support** - skills can trigger a session restart
# - **Window titles** - terminal tab shows `Claude: parent/dir`
# - **Labels** - `cw -l "my-task"` adds a label to the title
#
# Usage:
#   cw                    # launch claude with restart support
#   cw -l "my-project"    # launch with a label in the title
#   cw -p "fix the bug"   # pass a prompt through to claude
# ---

set -euo pipefail

SCRIPTS_DIR="$HOME/Bros/Projects/scripts"

if [[ ! -d "$SCRIPTS_DIR" ]]; then
    echo "Error: $SCRIPTS_DIR does not exist"
    exit 1
fi

if [[ ! -x "$SCRIPTS_DIR/cw" ]]; then
    echo "Error: $SCRIPTS_DIR/cw not found or not executable"
    exit 1
fi

# Check if already on PATH
if echo "$PATH" | tr ':' '\n' | grep -qx "$SCRIPTS_DIR"; then
    echo "Already on PATH: $SCRIPTS_DIR"
    echo ""
    echo "cw is ready to use:"
    echo "  $(command -v cw 2>/dev/null || echo "$SCRIPTS_DIR/cw")"
    exit 0
fi

# Detect shell profile
if [[ -f "$HOME/.zshrc" ]]; then
    PROFILE="$HOME/.zshrc"
elif [[ -f "$HOME/.bash_profile" ]]; then
    PROFILE="$HOME/.bash_profile"
elif [[ -f "$HOME/.bashrc" ]]; then
    PROFILE="$HOME/.bashrc"
else
    PROFILE="$HOME/.zshrc"
fi

echo "Adding $SCRIPTS_DIR to PATH in $PROFILE..."
echo "" >> "$PROFILE"
echo "# Bros shared scripts (cw, etc.)" >> "$PROFILE"
echo "export PATH=\"$SCRIPTS_DIR:\$PATH\"" >> "$PROFILE"

echo ""
echo "=== Done ==="
echo "Added to: $PROFILE"
echo "Run 'source $PROFILE' or open a new terminal to use cw."
