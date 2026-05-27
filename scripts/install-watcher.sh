#!/bin/bash
# Install the Brotherly notification system
#
# Sets up two macOS LaunchAgents:
#
# 1. **Request watcher** - monitors the requests directory and shows
#    dialogs when new requests arrive (Approve/Skip/View Script)
#
# 2. **Notification handler** - shows clickable macOS notifications
#    sent by Chris or his agents. Clicking opens the brotherly TUI
#    in Terminal.app.
#
# Also installs `terminal-notifier` via Homebrew for clickable
# notifications.
#
# The agents run automatically on login and trigger whenever new
# files appear in the watched directories.
# ---

set -euo pipefail

BROTHERLY_DIR="$HOME/Bros/Projects/brotherly"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$BROTHERLY_DIR/notifications"
mkdir -p "$BROTHERLY_DIR/logs"

# Install terminal-notifier for clickable notifications
BREW="/opt/homebrew/bin/brew"
if [[ -x "$BREW" ]]; then
    if ! "$BREW" list terminal-notifier &>/dev/null; then
        echo "Installing terminal-notifier..."
        "$BREW" install terminal-notifier
    else
        echo "terminal-notifier already installed."
    fi
else
    echo "Warning: Homebrew not found. Notifications will use fallback (non-clickable)."
fi

# Make helper scripts executable
chmod +x "$BROTHERLY_DIR/scripts/open-brotherly.sh" 2>/dev/null || true
chmod +x "$BROTHERLY_DIR/scripts/brotherly-watcher.py" 2>/dev/null || true
chmod +x "$BROTHERLY_DIR/scripts/brotherly-notification-handler.py" 2>/dev/null || true

# Install request watcher
WATCHER_PLIST="com.brotherly.watcher.plist"
echo ""
echo "Installing request watcher..."
launchctl unload "$LAUNCH_AGENTS_DIR/$WATCHER_PLIST" 2>/dev/null || true
cp "$BROTHERLY_DIR/launchd/$WATCHER_PLIST" "$LAUNCH_AGENTS_DIR/"
launchctl load "$LAUNCH_AGENTS_DIR/$WATCHER_PLIST"
echo "  Loaded: $WATCHER_PLIST"

# Install notification handler
NOTIF_PLIST="com.brotherly.notifications.plist"
echo ""
echo "Installing notification handler..."
launchctl unload "$LAUNCH_AGENTS_DIR/$NOTIF_PLIST" 2>/dev/null || true
cp "$BROTHERLY_DIR/launchd/$NOTIF_PLIST" "$LAUNCH_AGENTS_DIR/"
launchctl load "$LAUNCH_AGENTS_DIR/$NOTIF_PLIST"
echo "  Loaded: $NOTIF_PLIST"

echo ""
echo "=== Installed ==="
echo "Request watcher:      watching $BROTHERLY_DIR/requests/"
echo "Notification handler: watching $BROTHERLY_DIR/notifications/"
echo ""
echo "Both start automatically on login."

# Verify
echo ""
echo "Status:"
launchctl list | grep brotherly || echo "  Warning: agents may not have loaded."
