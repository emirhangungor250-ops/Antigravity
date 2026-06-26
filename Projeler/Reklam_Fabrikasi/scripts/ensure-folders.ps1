# Ensure machine-state folders exist on Windows.
#
# v1.3.0 split:
#   - Project work goes to .\Reklam Fabrikası\<numbered-folder>\ in whatever
#     folder Claude Code is open in. Skills create those lazily on first run.
#   - Machine state lives under $HOME\Reklam-Fabrikasi\_meta\. One per machine.
#
# This script only ensures the machine-state tree exists. It does NOT
# pre-create any numbered project folders, those are now per-project.

$ErrorActionPreference = "SilentlyContinue"

$root      = Join-Path $env:USERPROFILE "Reklam-Fabrikasi"
$metaDir   = Join-Path $root "_meta"
$stateDir  = Join-Path $metaDir ".state"
$setupDir  = Join-Path $stateDir "setup"
$venvsDir  = Join-Path $metaDir ".venvs"

foreach ($p in @($root, $metaDir, $stateDir, $setupDir, $venvsDir)) {
  if (-not (Test-Path $p)) {
    New-Item -ItemType Directory -Path $p -Force | Out-Null
  }
}

# v1.2.5 migration: move legacy ~\Reklam-Fabrikasi\.state into ~\Reklam-Fabrikasi\_meta\.state.
$legacyState = Join-Path $root ".state"
if (Test-Path $legacyState) {
  foreach ($f in @("install.log", "path-fixed.flag", "meta-ads-installed.flag", "fallback-install.log")) {
    $src = Join-Path $legacyState $f
    $dst = Join-Path $stateDir $f
    if ((Test-Path $src) -and -not (Test-Path $dst)) {
      Move-Item -Path $src -Destination $dst -Force
    }
  }
  $legacySetup = Join-Path $legacyState "setup"
  if (Test-Path $legacySetup) {
    Get-ChildItem -Path $legacySetup -File -ErrorAction SilentlyContinue | ForEach-Object {
      $dst = Join-Path $setupDir $_.Name
      if (-not (Test-Path $dst)) {
        Move-Item -Path $_.FullName -Destination $dst -Force
      }
    }
    if (-not (Get-ChildItem -Path $legacySetup -Force | Where-Object { $_.Name -ne "." -and $_.Name -ne ".." })) {
      Remove-Item -Path $legacySetup -Force
    }
  }
  if (-not (Get-ChildItem -Path $legacyState -Force | Where-Object { $_.Name -ne "." -and $_.Name -ne ".." })) {
    Remove-Item -Path $legacyState -Force
  }
}

$legacyVenvs = Join-Path $root ".venvs"
$legacyMetaAds = Join-Path $legacyVenvs "meta-ads"
$newMetaAds = Join-Path $venvsDir "meta-ads"
if ((Test-Path $legacyMetaAds) -and -not (Test-Path $newMetaAds)) {
  Move-Item -Path $legacyMetaAds -Destination $newMetaAds -Force
  if (Test-Path $legacyVenvs) {
    if (-not (Get-ChildItem -Path $legacyVenvs -Force | Where-Object { $_.Name -ne "." -and $_.Name -ne ".." })) {
      Remove-Item -Path $legacyVenvs -Force
    }
  }
}

Write-Host "[reklam-fabrikasi] Machine state ready at $metaDir"
exit 0
