#!/usr/bin/env bash
# resolve-claude-cli.sh
# Prints the absolute path to a working `claude` CLI binary on stdout.
# Exits 0 on success, 1 on failure with an error on stderr.
#
# Resolution order:
#   1. command -v claude (anything already on PATH)
#   2. /opt/homebrew/bin/claude, /usr/local/bin/claude
#   3. Latest version inside the macOS desktop app bundle
#   4. ~/.claude/local/claude (npm-style install)
#   5. ~/.local/bin/claude (custom install path)
#
# Usage:
#   CLAUDE_BIN="$(bash scripts/resolve-claude-cli.sh)" || exit 1
#   "$CLAUDE_BIN" --version

set -u

# 1. Already on PATH
if command -v claude >/dev/null 2>&1; then
  command -v claude
  exit 0
fi

# 2. Homebrew paths
for candidate in /opt/homebrew/bin/claude /usr/local/bin/claude; do
  if [ -x "$candidate" ]; then
    printf '%s\n' "$candidate"
    exit 0
  fi
done

# 3. macOS desktop app bundle. Pick the highest version.
APP_ROOT="$HOME/Library/Application Support/Claude/claude-code"
if [ -d "$APP_ROOT" ]; then
  LATEST="$(ls -1 "$APP_ROOT" 2>/dev/null \
    | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' \
    | sort -t. -k1,1n -k2,2n -k3,3n \
    | tail -n 1)"
  if [ -n "$LATEST" ]; then
    BUNDLED="$APP_ROOT/$LATEST/claude.app/Contents/MacOS/claude"
    if [ -x "$BUNDLED" ]; then
      printf '%s\n' "$BUNDLED"
      exit 0
    fi
  fi
fi

# 3b. claude-code-vm sibling location (some installs land here too)
VM_ROOT="$HOME/Library/Application Support/Claude/claude-code-vm"
if [ -d "$VM_ROOT" ]; then
  LATEST_VM="$(ls -1 "$VM_ROOT" 2>/dev/null \
    | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' \
    | sort -t. -k1,1n -k2,2n -k3,3n \
    | tail -n 1)"
  if [ -n "$LATEST_VM" ]; then
    VM_BIN="$VM_ROOT/$LATEST_VM/claude"
    if [ -x "$VM_BIN" ]; then
      printf '%s\n' "$VM_BIN"
      exit 0
    fi
  fi
fi

# 4. npm-style install
if [ -x "$HOME/.claude/local/claude" ]; then
  printf '%s\n' "$HOME/.claude/local/claude"
  exit 0
fi

# 5. ~/.local/bin
if [ -x "$HOME/.local/bin/claude" ]; then
  printf '%s\n' "$HOME/.local/bin/claude"
  exit 0
fi

printf 'Cannot find claude CLI. Make sure Claude Code is installed.\n' >&2
exit 1
