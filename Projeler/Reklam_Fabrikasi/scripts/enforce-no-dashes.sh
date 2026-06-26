#!/usr/bin/env bash
# Reklam Fabrikası em dash and en dash stripper.
#
# This script reads JSON from stdin per the Claude Code hooks contract.
# Claude Code 2.1.x sends a single JSON object on stdin to every hook.
# For PostToolUse on Write or Edit, the payload contains tool_input.file_path.
#
# The CLAUDE_TOOL_FILE_PATH env var does not exist on Claude Code 2.1.x.
# The fallback below only fires if stdin is empty, which would mean the
# host runtime reverted to env-var dispatch. Treat the fallback as defensive
# and unreliable, not as a supported path.

set -u

# Read full payload first so stdin is fully drained on every code path.
# Failing to drain stdin causes EPIPE on Claude Code 2.1.x.
PAYLOAD="$(cat 2>/dev/null || true)"

target=""

if [ -n "$PAYLOAD" ] && command -v jq >/dev/null 2>&1; then
  target="$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
fi

# Defensive fallback to the legacy env var. This is unreliable on
# Claude Code 2.1.x and only kicks in if stdin produced nothing.
if [ -z "$target" ]; then
  target="${CLAUDE_TOOL_FILE_PATH:-}"
fi

if [ -z "$target" ] || [ ! -f "$target" ]; then
  exit 0
fi

# Skip binary files and large media.
case "$target" in
  *.png|*.jpg|*.jpeg|*.mp4|*.webp|*.gif|*.zip|*.pdf)
    exit 0
    ;;
esac

# In place replacement, BSD and GNU sed compatible via a temp file.
tmp="$(mktemp)"
LC_ALL=en_US.UTF-8 sed -e 's/\xE2\x80\x94/, /g' -e 's/\xE2\x80\x93/, /g' "$target" > "$tmp" 2>/dev/null
if [ -s "$tmp" ]; then
  cat "$tmp" > "$target"
fi
rm -f "$tmp"

exit 0
