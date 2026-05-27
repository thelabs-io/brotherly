#!/bin/bash
# Install the cw (Claude wrapper) script
#
# Installs `cw`, a wrapper around `claude` that adds:
# - **Self-restart support** - skills can trigger a session restart
#   without losing your working directory
# - **Window titles** - terminal tab shows `Claude: parent/dir [pts/N]`
#   so you can tell sessions apart at a glance
# - **Labels** - `cw -l "my-task"` adds a label to the title
# - **CWD directives** - restarted sessions can change directory
#
# Installs to `/usr/local/bin/cw` (available to all users).
#
# Usage after install:
#   cw                    # launch claude with restart support
#   cw -l "my-project"    # launch with a label in the title
#   cw -p "fix the bug"   # pass a prompt through to claude
#
# Requires `claude` CLI to already be installed.
# ---

set -euo pipefail

INSTALL_DIR="/usr/local/bin"
SCRIPT_PATH="$INSTALL_DIR/cw"

if ! command -v claude &>/dev/null; then
    echo "Warning: 'claude' CLI not found in PATH."
    echo "cw wraps claude, so you'll need it installed before using cw."
    echo "Continuing with install anyway..."
    echo ""
fi

echo "Installing cw to $SCRIPT_PATH..."

cat > "$SCRIPT_PATH" << 'CWEOF'
#!/usr/bin/env bash
# cw - Claude wrapper with self-restart support and cwd in window title
set -uo pipefail

export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1
export CLAUDE_CODE_NO_FLICKER=1

label=""
passthrough=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -l|--label) label="$2"; shift 2 ;;
        *) passthrough+=("$1"); shift ;;
    esac
done

set_title() {
    local dir_name="${PWD##*/}"
    local parent_name
    parent_name="$(basename "$(dirname "$PWD")")"
    local pts
    pts="$(tty 2>/dev/null)" && pts="${pts#/dev/}" || pts="?"
    local suffix=""
    [[ -n "$label" ]] && suffix=" [$label]"
    suffix+=" [$pts]"
    printf '\e]0;Claude: %s/%s%s\a' "$parent_name" "$dir_name" "$suffix"
}

rf="/tmp/.claude-restart-$$"
export CLAUDE_RESTART_FILE="$rf"
args=(--dangerously-skip-permissions "${passthrough[@]}")

while true; do
    set_title
    rm -f "$rf"
    claude "${args[@]}" || true
    [[ -f "$rf" ]] || break
    mapfile -t args < "$rf"
    # Support directives: first lines starting with KEY: are consumed by cw
    while [[ ${#args[@]} -gt 0 && "${args[0]}" == *:* ]]; do
        case "${args[0]}" in
            CWD:*)
                new_cwd="${args[0]#CWD:}"
                args=("${args[@]:1}")
                cd "$new_cwd" || { echo "Failed to cd to $new_cwd"; break 2; }
                echo "Changed directory to: $(pwd)"
                ;;
            LABEL:*)
                label="${args[0]#LABEL:}"
                args=("${args[@]:1}")
                echo "Label updated to: $label"
                ;;
            *) break ;;
        esac
    done
    echo "Restarting Claude..."
    sleep 1
done

rm -f "$rf"
CWEOF

chmod 755 "$SCRIPT_PATH"

echo ""
echo "=== Installed ==="
echo "Location: $SCRIPT_PATH"
echo "Version: $(head -2 "$SCRIPT_PATH" | tail -1)"
echo ""
echo "Usage:"
echo "  cw                    # launch claude"
echo "  cw -l 'my-project'    # launch with a label"
echo "  cw -p 'fix the bug'   # pass a prompt to claude"
