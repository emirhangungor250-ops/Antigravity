#!/usr/bin/env bash
# Ensure machine-state folders exist on macOS or Linux.
#
# v1.3.0 split:
#   - Project work goes to ./Reklam Fabrikası/<numbered-folder>/ in whatever
#     folder Claude Code is open in. Skills create those lazily on first run.
#   - Machine state lives under ~/Reklam-Fabrikasi/_meta/ (install logs, install
#     flags, Python venvs, CLI PATH symlink flag). One per machine.
#
# This script only ensures the machine-state tree exists. It does NOT
# pre-create any numbered project folders, those are now per-project.

set -u

ROOT="$HOME/Reklam-Fabrikasi"
META_DIR="$ROOT/_meta"
STATE_DIR="$META_DIR/.state"
SETUP_DIR="$STATE_DIR/setup"
VENVS_DIR="$META_DIR/.venvs"

mkdir -p "$ROOT" "$META_DIR" "$STATE_DIR" "$SETUP_DIR" "$VENVS_DIR" 2>/dev/null || true

# v1.2.5 migration: if the legacy ~/Reklam-Fabrikasi/.state/ exists from prior
# versions, move install logs and flags into the new ~/Reklam-Fabrikasi/_meta/.state/
# location. Idempotent, only runs if the legacy dir is present.
LEGACY_STATE="$ROOT/.state"
if [ -d "$LEGACY_STATE" ]; then
  for f in install.log path-fixed.flag meta-ads-installed.flag fallback-install.log; do
    if [ -f "$LEGACY_STATE/$f" ] && [ ! -f "$STATE_DIR/$f" ]; then
      mv "$LEGACY_STATE/$f" "$STATE_DIR/$f" 2>/dev/null || true
    fi
  done
  if [ -d "$LEGACY_STATE/setup" ]; then
    for marker in "$LEGACY_STATE/setup"/*.done "$LEGACY_STATE/setup"/*.txt; do
      [ -f "$marker" ] || continue
      base="$(basename "$marker")"
      if [ ! -f "$SETUP_DIR/$base" ]; then
        mv "$marker" "$SETUP_DIR/$base" 2>/dev/null || true
      fi
    done
    rmdir "$LEGACY_STATE/setup" 2>/dev/null || true
  fi
  rmdir "$LEGACY_STATE" 2>/dev/null || true
fi

# Same migration for the legacy venv location.
LEGACY_VENVS="$ROOT/.venvs"
if [ -d "$LEGACY_VENVS" ] && [ ! -d "$VENVS_DIR/meta-ads" ] && [ -d "$LEGACY_VENVS/meta-ads" ]; then
  mv "$LEGACY_VENVS/meta-ads" "$VENVS_DIR/meta-ads" 2>/dev/null || true
  rmdir "$LEGACY_VENVS" 2>/dev/null || true
fi

echo "[reklam-fabrikasi] Machine state ready at $META_DIR"
exit 0
