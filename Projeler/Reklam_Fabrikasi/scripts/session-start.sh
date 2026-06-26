#!/usr/bin/env bash
# Reklam Fabrikası SessionStart wrapper.
#
# This script reads JSON from stdin per the Claude Code hooks contract.
# Claude Code 2.1.x sends a single JSON object on stdin to every hook.
# We do not need any of those fields, but stdin still has to be drained
# or the host process can EPIPE.
#
# The plugin directory is resolved from this script's own location via
# ${BASH_SOURCE[0]} so it does not depend on CLAUDE_PLUGIN_ROOT, which
# is unreliable on SessionStart per upstream Claude Code issue 27145.

set -u

# Drain stdin so the hook does not EPIPE on Claude Code 2.1.x.
cat >/dev/null 2>&1 || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. Ensure the per machine and per project folder layout exists.
if [ -f "$PLUGIN_DIR/scripts/ensure-folders.sh" ]; then
  bash "$PLUGIN_DIR/scripts/ensure-folders.sh" || true
fi

# 2. Put the bundled Claude CLI on PATH if not already done.
if [ -f "$PLUGIN_DIR/scripts/install-claude-on-path.sh" ] && [ ! -f "$HOME/Reklam-Fabrikasi/_meta/.state/path-fixed.flag" ]; then
  bash "$PLUGIN_DIR/scripts/install-claude-on-path.sh" >/dev/null 2>&1 || true
fi

# 3. Seed CLAUDE.md (brand memory) into the current project's brand
# folder if the folder exists and CLAUDE.md is missing. Idempotent and
# silent when there is nothing to do. Catches returning sessions in
# brand folders that pre-date the brand-memory feature.
if [ -f "$PLUGIN_DIR/scripts/seed-claude-md.sh" ]; then
  bash "$PLUGIN_DIR/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi

# 4. Lazy install the Meta Ads Python venv in the background.
if [ -f "$PLUGIN_DIR/scripts/install-meta-ads.sh" ]; then
  nohup bash "$PLUGIN_DIR/scripts/install-meta-ads.sh" "$PLUGIN_DIR" >/dev/null 2>&1 &
fi

exit 0
