#!/bin/bash
# Install the Brotherly request watcher
#
# Sets up a macOS LaunchAgent that watches for new brotherly
# requests and shows native notification dialogs when Chris
# sends a script for review.
#
# When a new request arrives, Matt sees a macOS dialog with the
# title, description, and Approve/Skip/View Script buttons.
# No need to open a terminal and run `brotherly` manually.
#
# The watcher runs automatically on login and triggers whenever
# a new file appears in the requests directory.
# ---

set -euo pipefail

BROTHERLY_DIR="$HOME/Bros/Projects/brotherly"
PLIST_SRC="$BROTHERLY_DIR/launchd/com.brotherly.watcher.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.brotherly.watcher.plist"

if [[ ! -f "$PLIST_SRC" ]]; then
    echo "Error: plist not found at $PLIST_SRC"
    echo "Run 'cd $BROTHERLY_DIR && git pull' first."
    exit 1
fi

if [[ ! -f "$BROTHERLY_DIR/scripts/brotherly-watcher.py" ]]; then
    echo "Error: watcher script not found"
    exit 1
fi

# Unload existing agent if running
if launchctl list | grep -q com.brotherly.watcher; then
    echo "Unloading existing watcher..."
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

echo "Installing LaunchAgent..."
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DST"

echo "Loading watcher..."
launchctl load "$PLIST_DST"

echo ""
echo "=== Installed ==="
echo "Plist: $PLIST_DST"
echo "Script: $BROTHERLY_DIR/scripts/brotherly-watcher.py"
echo "Watching: $BROTHERLY_DIR/requests/"
echo ""
echo "The watcher will show a dialog whenever Chris sends a new request."
echo "It starts automatically on login."

# Verify it's running
if launchctl list | grep -q com.brotherly.watcher; then
    echo ""
    echo "Status: running"
else
    echo ""
    echo "Warning: agent may not have loaded. Check with:"
    echo "  launchctl list | grep brotherly"
fi
