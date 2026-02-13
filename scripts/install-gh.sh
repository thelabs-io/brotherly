#!/bin/bash
# Install GitHub CLI
#
# Installs `gh` (GitHub CLI) via Homebrew.
# This is useful for managing repos, PRs, and issues from the terminal.
#
# Safe to re-run — Homebrew will skip if already installed.

set -euo pipefail

brew install gh
