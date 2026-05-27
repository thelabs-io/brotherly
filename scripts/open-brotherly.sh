#!/bin/bash
# Opens the brotherly TUI in the current terminal.
# Called by terminal-notifier when a notification is clicked.
cd "$HOME/Bros/Projects/brotherly" || exit 1
exec brotherly
