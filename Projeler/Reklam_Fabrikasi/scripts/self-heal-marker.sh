#!/usr/bin/env bash
# Reklam Fabrikası self-heal marker writer.
#
# This script reads JSON from stdin per the Claude Code hooks contract.
# Claude Code 2.1.x sends a single JSON object on stdin to every hook,
# containing session_id, cwd, hook_event_name, tool_name, tool_input,
# and tool_response. There is no PostToolUseFailure event, only PostToolUse,
# so this hook fires on every tool call and itself filters by exit code.
#
# Stale CLAUDE_TOOL_NAME, CLAUDE_TOOL_EXIT_CODE, and CLAUDE_TOOL_STDERR
# env vars do not exist on Claude Code 2.1.x. The canonical source is
# the stdin JSON.

set -u

# Read full payload first so stdin is fully drained even on the early exit
# path. Failing to drain stdin causes EPIPE on Claude Code 2.1.x.
PAYLOAD="$(cat 2>/dev/null || true)"

# If jq is missing, exit silently. Hooks must never block the user.
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

if [ -z "$PAYLOAD" ]; then
  exit 0
fi

EXIT_CODE="$(printf '%s' "$PAYLOAD" | jq -r '.tool_response.exit_code // empty' 2>/dev/null)"

# Only proceed when the tool actually failed. Exit 0, missing, or null means success.
if [ -z "$EXIT_CODE" ] || [ "$EXIT_CODE" = "0" ] || [ "$EXIT_CODE" = "null" ]; then
  exit 0
fi

TOOL="$(printf '%s' "$PAYLOAD" | jq -r '.tool_name // "unknown"' 2>/dev/null)"
STDERR="$(printf '%s' "$PAYLOAD" | jq -r '.tool_response.stderr // ""' 2>/dev/null)"

# Generate stable error ID: RF-YYYY-MM-DD-<4hex>
DATE_PART="$(date -u +%Y-%m-%d)"
HEX_PART="$(openssl rand -hex 2 2>/dev/null || head -c 4 /dev/urandom | xxd -p)"
ERROR_ID="RF-${DATE_PART}-${HEX_PART:0:4}"

# Marker location: per-machine state, not per-project.
MARKER_DIR="$HOME/.claude/plugins/reklam-fabrikasi"
mkdir -p "$MARKER_DIR"

# Truncate stderr to first 500 chars and escape for JSON.
SAFE_STDERR="$(printf '%s' "$STDERR" | head -c 500 | sed 's/"/\\"/g' | tr '\n' ' ')"

# Atomic write: tmp then rename.
cat > "$MARKER_DIR/last-error.json.tmp" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "error_id": "$ERROR_ID",
  "tool": "$TOOL",
  "exit_code": $EXIT_CODE,
  "stderr_truncated": "$SAFE_STDERR",
  "tier_reached": 4,
  "auto_heal_attempted": true,
  "auto_heal_succeeded": false,
  "phase": "A",
  "note": "Phase B will read this marker to generate structured DM template"
}
EOF

mv "$MARKER_DIR/last-error.json.tmp" "$MARKER_DIR/last-error.json"

# Exit 0 so the hook adds no noise to the conversation.
exit 0
