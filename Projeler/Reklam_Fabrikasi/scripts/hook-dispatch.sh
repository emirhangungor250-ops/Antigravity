#!/usr/bin/env bash
# Reklam Fabrikası cross-platform hook dispatcher.
#
# Takes a hook base name as $1 and routes to <name>.sh on Unix
# or <name>.ps1 on Windows. The plugin directory is resolved from
# this script's own location via ${BASH_SOURCE[0]}, so this dispatcher
# does not depend on CLAUDE_PLUGIN_ROOT (which the existing
# session-start wrapper documents as unreliable per upstream Claude
# Code issue 27145).
#
# Why this dispatcher exists: Claude Code 2.1.x on Windows Git Bash
# invokes hook commands by passing them through `bash -c "bash <cmd>"`,
# which prepends `bash ` to the script the inner bash actually parses.
# When a hook command starts with `if`, the prepended `bash ` makes
# `if` a regular argument rather than the start of an if-statement,
# and the bash parser then trips on the bare `then`/`else`/`fi`
# reserved words. By moving all if/case logic into a script file
# and reducing the hook command to a single path-plus-arg invocation,
# the prepend becomes harmless: `bash <path> <name>` is always a
# valid bash invocation.
#
# Stdin is passed through unchanged so the per-event scripts can
# read the Claude Code 2.1.x JSON payload as documented.

set -u

NAME="${1:-}"
if [ -z "$NAME" ]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

case "$(uname 2>/dev/null)" in
  Darwin|Linux)
    if [ -f "$PLUGIN_DIR/scripts/$NAME.sh" ]; then
      exec bash "$PLUGIN_DIR/scripts/$NAME.sh"
    fi
    ;;
  *)
    if [ -f "$PLUGIN_DIR/scripts/$NAME.ps1" ]; then
      exec powershell -NoProfile -ExecutionPolicy Bypass -File "$PLUGIN_DIR/scripts/$NAME.ps1"
    fi
    ;;
esac

exit 0
