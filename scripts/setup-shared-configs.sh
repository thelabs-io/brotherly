#!/bin/bash
# Set up shared config symlinks
#
# Links Matt's config directories to the shared `~/bros/shared/` tree so
# both brothers use the same Claude agents, skills, and Coderoo config.
#
# **What this does:**
#
# 1. Backs up any existing directories (renamed to `.bak`)
# 2. Creates symlinks:
#    - `~/.config/coderoo` → `~/bros/shared/coderoo-config`
#    - `~/.claude/agents` → `~/bros/shared/claude-agents`
#    - `~/.claude/skills` → `~/bros/shared/claude-skills`
# 3. Adds `source ~/bros/shared/shell-config.zsh` to `~/.zshrc` if not present
# 4. Fixes group-write permissions on `~/bros/projects/`
#
# Safe to re-run — skips symlinks that are already correct.

set -euo pipefail

link() {
    local target="$1"
    local link="$2"
    local parent
    parent="$(dirname "$link")"

    # Already correct symlink — skip
    if [ -L "$link" ] && [ "$(readlink "$link")" = "$target" ]; then
        echo "  already linked: $link"
        return
    fi

    # Back up existing file/dir/wrong-symlink
    if [ -e "$link" ] || [ -L "$link" ]; then
        echo "  backing up: $link -> ${link}.bak"
        mv "$link" "${link}.bak"
    fi

    mkdir -p "$parent"
    ln -s "$target" "$link"
    echo "  linked: $link -> $target"
}

echo "=== Setting up shared config symlinks ==="
link ~/bros/shared/coderoo-config ~/.config/coderoo
link ~/bros/shared/claude-agents   ~/.claude/agents
link ~/bros/shared/claude-skills   ~/.claude/skills

echo ""
echo "=== Updating ~/.zshrc ==="
if grep -q "source ~/bros/shared/shell-config.zsh" ~/.zshrc 2>/dev/null; then
    echo "  already present in ~/.zshrc"
else
    echo "" >> ~/.zshrc
    echo "# Shared Bros shell config" >> ~/.zshrc
    echo "source ~/bros/shared/shell-config.zsh" >> ~/.zshrc
    echo "  added to ~/.zshrc"
fi

echo ""
echo "=== Fixing group-write permissions ==="
chmod -R g+w ~/bros/projects/
echo "  done"

echo ""
echo "All done! Open a new terminal for shell config changes to take effect."
