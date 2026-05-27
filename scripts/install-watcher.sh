#!/bin/bash
# Install the Brotherly notification system
#
# Sets up a macOS LaunchAgent that shows clickable notifications
# when Chris or his agents send a message. Clicking a notification
# opens the brotherly TUI in Terminal.app so Matt can review and
# approve pending requests.
#
# Also installs `terminal-notifier` via Homebrew for clickable
# notifications.
#
# The agent runs automatically on login and triggers whenever new
# files appear in the notifications directory.
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
chmod +x "$BROTHERLY_DIR/scripts/brotherly-notification-handler.py" 2>/dev/null || true

# Unload old request watcher if present
launchctl unload "$LAUNCH_AGENTS_DIR/com.brotherly.watcher.plist" 2>/dev/null || true
rm -f "$LAUNCH_AGENTS_DIR/com.brotherly.watcher.plist"

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
echo "Notification handler: watching $BROTHERLY_DIR/notifications/"
echo "Starts automatically on login."

# Verify
echo ""
echo "Status:"
launchctl list | grep brotherly || echo "  Warning: agent may not have loaded."
