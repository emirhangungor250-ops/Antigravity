#!/usr/bin/env bash
# install-claude-on-path.sh
# One-time installer that puts the `claude` CLI on the user's PATH.
# Resolves the binary, creates a symlink in a writeable bin dir, and
# falls back to ~/.local/bin (with a ~/.zprofile PATH update) if the
# system bin dirs need sudo.
#
# Idempotent. Safe to run on every SessionStart.

set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOLVER="$SCRIPT_DIR/resolve-claude-cli.sh"

LOG_DIR="$HOME/Reklam-Fabrikasi/_meta/.state"
LOG_FILE="$LOG_DIR/install.log"
mkdir -p "$LOG_DIR"

log() {
  printf '[%s] install-claude-on-path: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG_FILE"
}

emit() {
  printf '%s\n' "$*"
  log "$*"
}

if [ ! -x "$RESOLVER" ]; then
  emit "ERROR: resolver not found at $RESOLVER"
  exit 1
fi

CLAUDE_BIN="$("$RESOLVER")" || {
  emit "ERROR: cannot resolve claude CLI. Make sure Claude Code is installed."
  exit 1
}

emit "Resolved claude CLI: $CLAUDE_BIN"

# If `claude` is already on PATH and points to our resolved binary (or any
# working location outside the desktop bundle), nothing to do.
EXISTING_ON_PATH="$(command -v claude 2>/dev/null || true)"
if [ -n "$EXISTING_ON_PATH" ]; then
  case "$EXISTING_ON_PATH" in
    *"/Library/Application Support/Claude/"*)
      emit "claude on PATH points inside app bundle. Will replace with stable symlink."
      ;;
    *)
      emit "claude already on PATH at $EXISTING_ON_PATH. Nothing to do."
      exit 0
      ;;
  esac
fi

# Decide target bin dir.
TARGET_DIR=""
for candidate in /opt/homebrew/bin /usr/local/bin; do
  if [ -d "$candidate" ] && [ -w "$candidate" ]; then
    TARGET_DIR="$candidate"
    break
  fi
done

USER_BIN="$HOME/.local/bin"
USED_USER_BIN=0
if [ -z "$TARGET_DIR" ]; then
  mkdir -p "$USER_BIN"
  TARGET_DIR="$USER_BIN"
  USED_USER_BIN=1
  emit "System bin dirs not writeable. Falling back to $USER_BIN."
fi

TARGET_LINK="$TARGET_DIR/claude"

if [ -L "$TARGET_LINK" ]; then
  CURRENT_TARGET="$(readlink "$TARGET_LINK" || true)"
  if [ "$CURRENT_TARGET" = "$CLAUDE_BIN" ]; then
    emit "Symlink at $TARGET_LINK already points to $CLAUDE_BIN. Nothing to do."
  else
    emit "Replacing stale symlink $TARGET_LINK (was: $CURRENT_TARGET)."
    ln -sf "$CLAUDE_BIN" "$TARGET_LINK"
  fi
elif [ -e "$TARGET_LINK" ]; then
  emit "WARNING: $TARGET_LINK exists as a real file (not a symlink). Refusing to overwrite."
  emit "         Move or delete it manually if you want Reklam Fabrikası symlink instead."
  # Do not bail. The user may have a working install we should not touch.
  exit 0
else
  ln -sf "$CLAUDE_BIN" "$TARGET_LINK"
  emit "Created symlink $TARGET_LINK -> $CLAUDE_BIN"
fi

# If we used ~/.local/bin, append it to ~/.zprofile and ~/.bash_profile so
# fresh login shells pick it up. Idempotent guard via marker comment.
if [ "$USED_USER_BIN" -eq 1 ]; then
  MARKER="# Reklam Fabrikası: ensure ~/.local/bin on PATH"
  for profile in "$HOME/.zprofile" "$HOME/.bash_profile" "$HOME/.profile"; do
    if [ ! -f "$profile" ]; then
      continue
    fi
    if ! grep -Fq "$MARKER" "$profile"; then
      {
        printf '\n%s\n' "$MARKER"
        printf 'case ":$PATH:" in *":%s:"*) ;; *) export PATH="%s:$PATH" ;; esac\n' "$USER_BIN" "$USER_BIN"
      } >> "$profile"
      emit "Appended PATH update to $profile."
    fi
  done
  # Make sure at least one profile contains the line. Create ~/.zprofile if
  # none exist (zsh is the macOS default since Catalina).
  if [ ! -f "$HOME/.zprofile" ] && [ ! -f "$HOME/.bash_profile" ] && [ ! -f "$HOME/.profile" ]; then
    {
      printf '%s\n' "$MARKER"
      printf 'case ":$PATH:" in *":%s:"*) ;; *) export PATH="%s:$PATH" ;; esac\n' "$USER_BIN" "$USER_BIN"
    } > "$HOME/.zprofile"
    emit "Created ~/.zprofile with PATH update."
  fi
fi

# Verify in a fresh non-interactive login shell.
VERIFY_OUT="$(PATH="$TARGET_DIR:$PATH" bash -lc 'command -v claude && claude --version' 2>&1 || true)"
if printf '%s' "$VERIFY_OUT" | grep -q "Claude Code"; then
  emit "VERIFIED: claude --version reports: $(printf '%s' "$VERIFY_OUT" | tail -n 1)"
  # Drop the success flag so SessionStart can skip on subsequent runs.
  printf '%s\n' "$CLAUDE_BIN" > "$LOG_DIR/path-fixed.flag"
  exit 0
else
  emit "WARNING: verification could not confirm claude --version. Output: $VERIFY_OUT"
  exit 1
fi
