#!/bin/bash
# Migrate brotherly to Projects directory
#
# Moves brotherly from `/Users/matt/Bros/brotherly` to
# `/Users/matt/Bros/Projects/brotherly` to live alongside
# other shared projects.
#
# This script:
# 1. Updates Matt's config to point to the new path
# 2. Reinstalls the `brotherly` CLI from the new location
# 3. Removes the old directory
#
# Chris's config and CLI are already updated.
# ---

set -euo pipefail

NEW_PATH="/Users/matt/Bros/Projects/brotherly"
OLD_PATH="/Users/matt/Bros/brotherly"
CONFIG="$HOME/.config/brotherly/config.json5"

# Verify new location exists
if [ ! -f "$NEW_PATH/pyproject.toml" ]; then
    echo "ERROR: $NEW_PATH does not exist or is incomplete"
    exit 1
fi

# Update Matt's config
echo "Updating config..."
mkdir -p "$(dirname "$CONFIG")"
cat > "$CONFIG" << 'EOF'
{
    "data_dir": "/Users/matt/Bros/Projects/brotherly"
}
EOF
echo "  Config updated: $CONFIG"

# Reinstall brotherly CLI from new path
echo ""
echo "Reinstalling brotherly CLI..."
uv tool uninstall brotherly
uv tool install -e "$NEW_PATH"

# Verify new install works
echo ""
echo "Verifying..."
brotherly list

# Remove old directory
echo ""
echo "Removing old directory: $OLD_PATH"
rm -rf "$OLD_PATH"

echo ""
echo "Done! brotherly now lives at $NEW_PATH"
