# resolve-claude-cli.ps1
# Prints the absolute path to a working `claude` CLI binary on stdout.
# Exits 0 on success, 1 on failure with an error on stderr.
#
# Resolution order:
#   1. Get-Command claude
#   2. $env:USERPROFILE\.local\bin\claude.exe (official claude.ai/install.ps1 path)
#   3. $env:LOCALAPPDATA\Programs\Claude\claude-code\<version>\claude.exe
#   4. $env:APPDATA\Claude\claude-code\<version>\claude.exe (alt location)
#
# Usage:
#   $claudeBin = & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\resolve-claude-cli.ps1
#   if ($LASTEXITCODE -ne 0) { exit 1 }
#   & $claudeBin --version

$ErrorActionPreference = "Stop"

# 1. Already on PATH
$cmd = Get-Command claude -ErrorAction SilentlyContinue
if ($cmd) {
  Write-Output $cmd.Source
  exit 0
}

# 2. Official install path
$officialPath = Join-Path $env:USERPROFILE ".local\bin\claude.exe"
if (Test-Path $officialPath) {
  Write-Output $officialPath
  exit 0
}

# 3. Local AppData desktop bundle. Pick highest version.
$bundleRoots = @(
  (Join-Path $env:LOCALAPPDATA "Programs\Claude\claude-code"),
  (Join-Path $env:APPDATA      "Claude\claude-code")
)
foreach ($root in $bundleRoots) {
  if (Test-Path $root) {
    $versions = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -match '^\d+\.\d+\.\d+' } |
      Sort-Object {
        $parts = $_.Name.Split('.')
        [version]("{0}.{1}.{2}" -f $parts[0], $parts[1], $parts[2])
      }
    if ($versions) {
      $latest = $versions[-1]
      $candidate = Join-Path $latest.FullName "claude.exe"
      if (Test-Path $candidate) {
        Write-Output $candidate
        exit 0
      }
    }
  }
}

[Console]::Error.WriteLine("Cannot find claude CLI. Make sure Claude Code is installed.")
exit 1
