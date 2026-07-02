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
# **Blacklisted skills** (22 - Chris-specific or not useful for Matt):
# agent-monitor, agent-teams, bus-arrival-monitor, claude-code-docs,
# easy-mode, get-feedback, gnome-extension-creator, iterative-compaction,
# maintenance-queue, move-session, new-convo, priority-synthesis,
# remember-this, report-hook-bug, review-sessions, self-awareness,
# self-improvement, signal-send, signal-voice-message,
# sync-runtime-config, synthesize, template-skill
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
    easy-mode
    get-feedback
    gnome-extension-creator
    iterative-compaction
    maintenance-queue
    move-session
    new-convo
    priority-synthesis
    remember-this
    report-hook-bug
    review-sessions
    self-awareness
    self-improvement
    signal-send
    signal-voice-message
    sync-runtime-config
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

# Destination top-level dirs are owned by matt (chris writes via group/ACL),
# so rsync must not try to set perms/owner/times on dirs it doesn't own.
# -L materializes symlinked skills (their targets don't exist on this machine).
RSYNC_OPTS=(-rLtv --no-perms --no-owner --no-group --omit-dir-times)

echo ""
echo "Copying agents..."
rsync "${RSYNC_OPTS[@]}" --exclude '.*' "$CHRIS_CLAUDE/agents/" "$MATT_CLAUDE/agents/"

echo ""
echo "Copying skills..."
exclude_args=()
for skill in "${BLACKLIST[@]}"; do
    exclude_args+=(--exclude "$skill")
done
rsync "${RSYNC_OPTS[@]}" --exclude '.*' --exclude '*.zip' --exclude '__pycache__' \
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
# Some files/dirs are matt-owned and can't be chmod'd from chris - that's fine.
chmod -R g+w "$MATT_CLAUDE/skills" 2>/dev/null || true
chmod -R g+w "$MATT_CLAUDE/agents" 2>/dev/null || true

echo ""
echo "=== Summary ==="
echo "Agents: $(find "$MATT_CLAUDE/agents" -name '*.md' -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')"
echo "Skills: $(find "$MATT_CLAUDE/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
echo "Blacklisted: ${#BLACKLIST[@]} skills skipped"
echo "Done! Installed to $MATT_CLAUDE"
