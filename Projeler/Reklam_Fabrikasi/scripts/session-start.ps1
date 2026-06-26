# Reklam Fabrikası SessionStart wrapper, Windows variant.
#
# This script reads JSON from stdin per the Claude Code hooks contract.
# Claude Code 2.1.x sends a single JSON object on stdin to every hook.
# We do not need any of those fields, but stdin still has to be drained
# or the host process can EPIPE.
#
# The plugin directory is resolved from this script's own location via
# $PSScriptRoot so it does not depend on CLAUDE_PLUGIN_ROOT, which is
# unreliable on SessionStart per upstream Claude Code issue 27145.

$ErrorActionPreference = 'SilentlyContinue'

# Drain stdin so the hook does not EPIPE on Claude Code 2.1.x.
[Console]::In.ReadToEnd() | Out-Null

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$pluginDir = Split-Path -Parent $scriptDir
$scriptsDir = Join-Path $pluginDir 'scripts'

# 1. Ensure the per machine and per project folder layout exists.
$ensureScript = Join-Path $scriptsDir 'ensure-folders.ps1'
if (Test-Path -LiteralPath $ensureScript) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureScript | Out-Null
}

# 2. Put the bundled Claude CLI on PATH if not already done.
$pathFlag = Join-Path $env:USERPROFILE 'Reklam-Fabrikasi\_meta\.state\path-fixed.flag'
$pathInstaller = Join-Path $scriptsDir 'install-claude-on-path.ps1'
if ((Test-Path -LiteralPath $pathInstaller) -and (-not (Test-Path -LiteralPath $pathFlag))) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $pathInstaller | Out-Null
}

# 3. Seed CLAUDE.md (brand memory) into the current project's brand
# folder if the folder exists and CLAUDE.md is missing. Idempotent and
# silent when there is nothing to do. Catches returning sessions in
# brand folders that pre-date the brand-memory feature.
$seedScript = Join-Path $scriptsDir 'seed-claude-md.ps1'
if (Test-Path -LiteralPath $seedScript) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $seedScript | Out-Null
}

# 4. Lazy install the Meta Ads Python venv in the background.
$metaInstaller = Join-Path $scriptsDir 'install-meta-ads.ps1'
if (Test-Path -LiteralPath $metaInstaller) {
    Start-Process -FilePath 'powershell' `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $metaInstaller, '-PluginRoot', $pluginDir) `
        -WindowStyle Hidden | Out-Null
}

exit 0
