#!/bin/bash
# Fix group-write permissions for shared directories
#
# Sets macOS ACLs on `~/Bros/` and `~/.claude/skills/` and
# `~/.claude/agents/` so that any file created inside these
# directories inherits group-write access for the `bros` group.
#
# This means Chris can update skills, agents, and shared project
# files remotely without needing Matt to approve each change.
#
# Also fixes existing files that are missing group-write.
# ---

set -euo pipefail

DIRS=(
    "$HOME/Bros"
    "$HOME/.claude/skills"
    "$HOME/.claude/agents"
)

ACL_ENTRY="group:bros allow list,add_file,search,add_subdirectory,delete_child,readattr,writeattr,readextattr,writeextattr,readsecurity,file_inherit,directory_inherit"

for dir in "${DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
        echo "Skipping (not found): $dir"
        continue
    fi

    echo "Fixing existing permissions: $dir"
    chmod -R g+w "$dir" 2>/dev/null || true

    echo "Setting inheritable ACL: $dir"
    chmod +a "$ACL_ENTRY" "$dir"

    echo "  Done: $dir"
    echo ""
done

echo "=== Verification ==="
for dir in "${DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "$dir:"
        ls -le -d "$dir" 2>/dev/null | head -3
        echo ""
    fi
done

echo "Done! New files in these directories will inherit group-write for bros."
