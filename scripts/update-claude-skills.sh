#!/bin/bash
# Update Claude Code agents and skills
#
# Syncs Chris's Claude Code agents and skills to Matt's `~/.claude/`
# directory, **skipping** skills that are specific to Chris's setup.
#
# **Agents** - Custom subagent definitions for specialized tasks like
# bug hunting, code review, research, and more.
#
# **Skills** - Slash-command workflows for TDD, deep research,
# session management, debugging, and more.
#
# **Blacklisted skills** (19 - Chris-specific or not useful for Matt):
# agent-monitor, agent-teams, bus-arrival-monitor, claude-code-docs,
# get-feedback, gnome-extension-creator, iterative-compaction,
# maintenance-queue, move-session, new-convo, priority-synthesis,
# remember-this, review-sessions, self-awareness, self-improvement,
# signal-send, signal-voice-message, synthesize, template-skill
#
# Also sets group-write permissions on Matt's skills directory so
# Chris can manage skills remotely.
#
# Safe to re-run - overwrites with latest versions.
# ---

set -euo pipefail

CHRIS_CLAUDE="/Users/chris/.claude"
MATT_CLAUDE="/Users/matt/.claude"

BLACKLIST=(
    agent-monitor
    agent-teams
    bus-arrival-monitor
    claude-code-docs
    get-feedback
    gnome-extension-creator
    iterative-compaction
    maintenance-queue
    move-session
    new-convo
    priority-synthesis
    remember-this
    review-sessions
    self-awareness
    self-improvement
    signal-send
    signal-voice-message
    synthesize
    template-skill
)

echo "Creating directories..."
mkdir -p "$MATT_CLAUDE/agents"
mkdir -p "$MATT_CLAUDE/skills"

echo ""
echo "Fixing permissions on existing files first..."
chmod -R g+w "$MATT_CLAUDE/skills" 2>/dev/null || true
chmod -R g+w "$MATT_CLAUDE/agents" 2>/dev/null || true

echo ""
echo "Copying agents..."
rsync -av --exclude '.*' "$CHRIS_CLAUDE/agents/" "$MATT_CLAUDE/agents/"

echo ""
echo "Copying skills..."
exclude_args=()
for skill in "${BLACKLIST[@]}"; do
    exclude_args+=(--exclude "$skill")
done
rsync -av --exclude '.*' --exclude '*.zip' --exclude '__pycache__' \
    "${exclude_args[@]}" \
    "$CHRIS_CLAUDE/skills/" "$MATT_CLAUDE/skills/"

echo ""
echo "Removing blacklisted skills that may exist from previous installs..."
for skill in "${BLACKLIST[@]}"; do
    if [[ -d "$MATT_CLAUDE/skills/$skill" ]]; then
        rm -rf "$MATT_CLAUDE/skills/$skill"
        echo "  Removed: $skill"
    fi
done

echo ""
echo "Setting group-write permissions on skills directory..."
chmod -R g+w "$MATT_CLAUDE/skills"
chmod -R g+w "$MATT_CLAUDE/agents"

echo ""
echo "=== Summary ==="
echo "Agents: $(find "$MATT_CLAUDE/agents" -name '*.md' -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')"
echo "Skills: $(find "$MATT_CLAUDE/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
echo "Blacklisted: ${#BLACKLIST[@]} skills skipped"
echo "Done! Installed to $MATT_CLAUDE"
