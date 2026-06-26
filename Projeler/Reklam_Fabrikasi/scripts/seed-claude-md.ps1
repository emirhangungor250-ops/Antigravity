# Seed a starter CLAUDE.md into .\Reklam Fabrikası\ if the brand folder has
# been confirmed by a skill and no CLAUDE.md exists yet.
#
# This file is the brand's living rulebook. Claude Code auto-loads it
# whenever the brand folder is in context, so any rule captured here
# applies to every future session and every future skill run.
#
# Called from two places:
#   1. SessionStart hook (catches returning sessions in brand folders
#      that pre-date this feature, or where the FIRST-RUN seed missed)
#   2. Each skill's FIRST-RUN PROTECTION block, right after the brand
#      folder is confirmed and folder-confirmed.flag is written
#
# Idempotent. Exits 0 silently if there is nothing to do. Safe to call
# repeatedly. Never overwrites an existing CLAUDE.md.

$ErrorActionPreference = "SilentlyContinue"

# Resolve the plugin root from this script's own location. Reliable in
# every context, unlike CLAUDE_PLUGIN_ROOT which is broken in
# SessionStart per upstream Claude Code issue 27145.
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$pluginDir = Split-Path -Parent $scriptDir
$template = Join-Path $pluginDir "skills\_shared\claude-md-template.md"

# Resolve the project's brand folder. We do NOT create it here, that is
# the responsibility of each skill's FIRST-RUN PROTECTION block which
# asks the member to confirm before any folder is created.
$projectRoot = Join-Path (Get-Location).Path "Reklam Fabrikası"
$claudeMd = Join-Path $projectRoot "CLAUDE.md"

# Only seed if the brand folder already exists. The skill has already
# asked the member, dropped folder-confirmed.flag, and created the
# folder tree. If the folder is missing, we have nothing to attach the
# brand memory to.
if (-not (Test-Path -LiteralPath $projectRoot)) { exit 0 }

# Never overwrite an existing CLAUDE.md. Once seeded, the file belongs
# to the brand and Claude self-maintains it from there.
if (Test-Path -LiteralPath $claudeMd) { exit 0 }

# Prefer the bundled template when available. Falls back to an inline
# minimal version if the template file is missing (defensive, should
# not happen in a healthy install).
if (Test-Path -LiteralPath $template) {
    Copy-Item -LiteralPath $template -Destination $claudeMd -Force
} else {
    $fallback = @'
# Brand memory for Reklam Fabrikası

This file is the brand's living rulebook. Claude self-maintains it as
the member uses the plugin.

## How to maintain this file (instructions to Claude)

When the member states a brand preference, constraint, or correction,
use the Edit tool to update this file. If the new input contradicts an
existing rule, replace the old rule. If it overlaps, merge. If it is
new, append to the right section below with today's date. After every
change, say one short line so the member can verify.

## Brand Rules

(empty)

## Forbidden Words and Phrases

(empty)

## Visual Rules

(empty)

## Last reviewed

(auto-updated when this file is changed)
'@
    Set-Content -LiteralPath $claudeMd -Value $fallback -Encoding UTF8
}

# Stamp Last reviewed with today's UTC date so the member can tell when
# the file was last touched. Best-effort, never fail the script over it.
try {
    $today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    if ($today -and (Test-Path -LiteralPath $claudeMd)) {
        $content = Get-Content -LiteralPath $claudeMd -Raw
        $updated = [regex]::Replace($content, '\(auto-updated when this file is changed[^)]*\)', $today)
        if ($updated -ne $content) {
            Set-Content -LiteralPath $claudeMd -Value $updated -Encoding UTF8
        }
    }
} catch {
    # Stamp failure is non-fatal, the file is still seeded.
}

Write-Host "[reklam-fabrikasi] Brand memory seeded at $claudeMd"
exit 0
