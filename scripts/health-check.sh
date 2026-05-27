#!/bin/bash
# Health check for Matt's brotherly setup
#
# Verifies that all brotherly components are installed and working:
# - terminal-notifier
# - notification handler LaunchAgent
# - cw wrapper script
# - coderoo
# - Claude Code skills and agents
# - group permissions
#
# Reports status for each component. Does not modify anything.
# ---

set -euo pipefail

BROTHERLY_DIR="$HOME/Bros/Projects/brotherly"
OK="\033[1;32m✓\033[0m"
FAIL="\033[1;31m✗\033[0m"
WARN="\033[1;33m!\033[0m"

check() {
    local label="$1"
    local result="$2"
    if [[ "$result" == "ok" ]]; then
        echo -e "  $OK $label"
    elif [[ "$result" == "warn" ]]; then
        echo -e "  $WARN $label"
    else
        echo -e "  $FAIL $label"
    fi
}

echo "=== Brotherly Health Check ==="
echo ""

# terminal-notifier
echo "Notifications:"
if command -v terminal-notifier &>/dev/null || [[ -x /opt/homebrew/bin/terminal-notifier ]]; then
    check "terminal-notifier installed" "ok"
else
    check "terminal-notifier NOT installed" "fail"
fi

if launchctl list 2>/dev/null | grep -q com.brotherly.notifications; then
    check "notification handler LaunchAgent loaded" "ok"
else
    check "notification handler LaunchAgent NOT loaded" "fail"
fi

if launchctl list 2>/dev/null | grep -q com.brotherly.watcher; then
    check "old request watcher still loaded (should be removed)" "warn"
else
    check "old request watcher not present" "ok"
fi

if [[ -d "$BROTHERLY_DIR/notifications" ]]; then
    pending_notifs=$(ls "$BROTHERLY_DIR/notifications/"*.json 2>/dev/null | wc -l | tr -d ' ')
    check "notifications dir exists ($pending_notifs pending)" "ok"
else
    check "notifications dir missing" "fail"
fi

echo ""
echo "CLI Tools:"
if command -v brotherly &>/dev/null; then
    check "brotherly CLI" "ok"
else
    check "brotherly CLI not in PATH" "fail"
fi

if command -v cw &>/dev/null; then
    check "cw wrapper" "ok"
elif [[ -x "$HOME/Bros/Projects/scripts/cw" ]]; then
    check "cw exists but not in PATH" "warn"
else
    check "cw not found" "fail"
fi

if command -v coderoo &>/dev/null; then
    check "coderoo CLI" "ok"
else
    check "coderoo CLI not in PATH" "fail"
fi

if command -v claude &>/dev/null; then
    check "claude CLI" "ok"
else
    check "claude CLI not in PATH" "fail"
fi

echo ""
echo "Claude Code:"
skills_count=$(find "$HOME/.claude/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
agents_count=$(find "$HOME/.claude/agents" -name '*.md' -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')
check "$skills_count skills installed" "ok"
check "$agents_count agents installed" "ok"

# Check group-write on skills
if [[ -w "$HOME/.claude/skills" ]]; then
    check "skills dir writable" "ok"
else
    check "skills dir NOT writable by group" "fail"
fi

echo ""
echo "Permissions:"
skills_acl=$(ls -le -d "$HOME/.claude/skills" 2>/dev/null | grep -c "bros allow")
bros_acl=$(ls -le -d "$HOME/Bros" 2>/dev/null | grep -c "bros allow")
if [[ "$skills_acl" -gt 0 ]]; then
    check "ACL on ~/.claude/skills" "ok"
else
    check "ACL missing on ~/.claude/skills" "fail"
fi
if [[ "$bros_acl" -gt 0 ]]; then
    check "ACL on ~/Bros" "ok"
else
    check "ACL missing on ~/Bros" "fail"
fi

echo ""
echo "Git Repos:"
for repo in brotherly coderoo; do
    dir="$HOME/Bros/Projects/$repo"
    if [[ -d "$dir/.git" ]]; then
        branch=$(cd "$dir" && git branch --show-current 2>/dev/null)
        commit=$(cd "$dir" && git log --oneline -1 2>/dev/null)
        check "$repo ($branch): $commit" "ok"
    else
        check "$repo repo not found" "fail"
    fi
done

echo ""
echo "System:"
mem_free=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
mem_free_mb=$(( mem_free * 16384 / 1048576 ))
echo "  Free memory: ${mem_free_mb} MB"
echo "  Uptime: $(uptime | sed 's/.*up /up /' | sed 's/,.*//')"
echo ""
