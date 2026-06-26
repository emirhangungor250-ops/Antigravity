# install-claude-on-path.ps1
# Adds the directory containing the resolved `claude.exe` to the user PATH
# (HKCU\Environment) and refreshes the current session.
#
# Idempotent. Safe to run on every SessionStart.

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$resolver  = Join-Path $scriptDir "resolve-claude-cli.ps1"

$logDir  = Join-Path $env:USERPROFILE "Reklam-Fabrikasi\_meta\.state"
$logFile = Join-Path $logDir "install.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log([string]$msg) {
  $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  $line  = "[$stamp] install-claude-on-path: $msg"
  Add-Content -Path $logFile -Value $line
  Write-Output $msg
}

if (-not (Test-Path $resolver)) {
  Write-Log "ERROR: resolver not found at $resolver"
  exit 1
}

$claudeBin = & powershell -NoProfile -ExecutionPolicy Bypass -File $resolver
if ($LASTEXITCODE -ne 0 -or -not $claudeBin) {
  Write-Log "ERROR: cannot resolve claude CLI. Make sure Claude Code is installed."
  exit 1
}
$claudeBin = $claudeBin.Trim()
Write-Log "Resolved claude CLI: $claudeBin"

$claudeDir = Split-Path -Parent $claudeBin

# Read current user PATH from registry (avoids the merged HKLM+HKCU view).
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }

$pathParts = $userPath.Split(';') | Where-Object { $_ -ne "" }
if ($pathParts -contains $claudeDir) {
  Write-Log "User PATH already contains $claudeDir. Nothing to do."
} else {
  $newPath = if ($userPath.TrimEnd(';') -eq "") { $claudeDir } else { $userPath.TrimEnd(';') + ";" + $claudeDir }
  [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
  Write-Log "Appended $claudeDir to user PATH."
}

# Refresh current session PATH.
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$env:Path = "$machinePath;" + [Environment]::GetEnvironmentVariable("Path", "User")

# Verify.
try {
  $version = & claude --version 2>&1
  if ($LASTEXITCODE -eq 0) {
    Write-Log "VERIFIED: claude --version reports: $version"
    Set-Content -Path (Join-Path $logDir "path-fixed.flag") -Value $claudeBin
    exit 0
  } else {
    Write-Log "WARNING: claude --version returned exit $LASTEXITCODE. Output: $version"
    exit 1
  }
} catch {
  Write-Log "WARNING: claude --version threw: $_"
  exit 1
}
