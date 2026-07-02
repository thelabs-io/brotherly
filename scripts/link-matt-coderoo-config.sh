#!/bin/bash
# Connect Coderoo to a shared global config
#
# Gives your Coderoo install a global config directory that Chris can
# keep updated remotely, by linking:
#
#     ~/.config/coderoo  ->  ~/Bros/shared/coderoo-config-matt
#
# The target is a config curated **for your setup** (Claude Code, Codex,
# and soon cursor-agent) - orchestration agents, delegation workflow
# instructions, and a minimal global config. It contains no references
# to Chris's machines or tools.
#
# What this script does:
#
# 1. If you already have a `~/.config/coderoo`, it is backed up to
#    `~/.config/coderoo.backup-<timestamp>` - nothing is deleted.
# 2. Creates the symlink.
# 3. Smoke-tests that `coderoo` still runs; if it doesn't, the backup
#    is restored automatically and the link is removed.
#
# Reversible: remove the symlink and rename the backup back.
# Touches only `~/.config/coderoo`. No sudo.
#
# prep: chmod -R g+rwX ~/Bros/shared/coderoo-config-matt/
# ---

set -uo pipefail   # deliberately no -e: report and continue

TARGET="$HOME/Bros/shared/coderoo-config-matt"
CFG="$HOME/.config/coderoo"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$CFG.backup-$STAMP"
fails=0

echo "== Linking Coderoo global config =="

# 1. Target must exist and be readable
if [[ ! -d "$TARGET" ]]; then
    echo "ERROR: target $TARGET does not exist - nothing changed."
    exit 1
fi
if [[ ! -r "$TARGET/global.config.json5" ]]; then
    echo "ERROR: cannot read $TARGET/global.config.json5 - permissions problem, nothing changed."
    exit 1
fi
echo "Target OK: $TARGET"

# 2. Handle any existing ~/.config/coderoo
restored_note=""
if [[ -L "$CFG" ]]; then
    current="$(readlink "$CFG")"
    if [[ "$current" == "$TARGET" ]]; then
        echo "Symlink already in place - nothing to do."
        exit 0
    fi
    echo "Existing symlink points at: $current - backing it up."
    mv "$CFG" "$BACKUP" || { echo "ERROR: could not move existing symlink."; exit 1; }
    restored_note="previous symlink -> $current"
elif [[ -e "$CFG" ]]; then
    echo "Existing config found. Contents (top level):"
    ls -la "$CFG" 2>/dev/null | sed 's/^/    /'
    mv "$CFG" "$BACKUP" || { echo "ERROR: could not back up existing config."; exit 1; }
    echo "Backed up to: $BACKUP"
    restored_note="previous config dir"
else
    echo "No existing ~/.config/coderoo - clean install."
fi

# 3. Create the symlink
if ln -s "$TARGET" "$CFG"; then
    echo "Created: $CFG -> $TARGET"
else
    echo "ERROR: symlink creation failed."
    ((fails++))
fi

# 4. Smoke test - coderoo must still run
if command -v coderoo >/dev/null 2>&1; then
    if coderoo --help >/dev/null 2>&1; then
        echo "Smoke test: coderoo runs OK with the new config."
    else
        echo "ERROR: coderoo failed to run with the new config - rolling back."
        rm -f "$CFG"
        if [[ -n "$restored_note" && -e "$BACKUP" ]]; then
            mv "$BACKUP" "$CFG" && echo "Restored $restored_note."
        fi
        exit 1
    fi
else
    echo "NOTE: coderoo CLI not on PATH in this shell - skipped smoke test."
fi

# 5. Summary
echo ""
echo "== Summary =="
echo "Link: $(readlink "$CFG" 2>/dev/null || echo MISSING)"
[[ -n "$restored_note" ]] && echo "Backup kept at: $BACKUP ($restored_note)"
echo "Failures: $fails"
exit "$fails"
