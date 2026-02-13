#!/bin/bash
# Install Claude Code agents and skills
#
# Copies Chris's Claude Code agents and skills to Matt's `~/.claude/` directory
# using `rsync` for reliable cross-user copying.
#
# **Agents** (12): Custom subagent definitions for specialized tasks like
# bug hunting, code review, research, and more.
#
# **Skills** (25): Slash-command workflows for TDD, deep research,
# session management, debugging, and more.
#
# These are the same agents and skills Chris uses. They extend what
# Claude Code can do from the terminal.
#
# Safe to re-run — overwrites with latest versions.
# ---

set -euo pipefail

CHRIS_CLAUDE="/Users/chris/.claude"
MATT_CLAUDE="/Users/matt/.claude"

echo "Creating directories..."
mkdir -p "$MATT_CLAUDE/agents"
mkdir -p "$MATT_CLAUDE/skills"

echo ""
echo "Copying agents..."
rsync -av --exclude '.*' "$CHRIS_CLAUDE/agents/" "$MATT_CLAUDE/agents/"

echo ""
echo "Copying skills..."
rsync -av --exclude '.*' --exclude '*.zip' --exclude '__pycache__' "$CHRIS_CLAUDE/skills/" "$MATT_CLAUDE/skills/"

echo ""
echo "=== Summary ==="
echo "Agents: $(ls "$MATT_CLAUDE/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Skills: $(ls -d "$MATT_CLAUDE/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "Done! Installed to $MATT_CLAUDE"
