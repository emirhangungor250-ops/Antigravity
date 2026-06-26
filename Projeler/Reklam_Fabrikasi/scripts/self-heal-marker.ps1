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
# the stdin JSON, parsed with ConvertFrom-Json.

$ErrorActionPreference = "SilentlyContinue"

# Read full payload first so stdin is fully drained even on the early exit
# path. Failing to drain stdin causes EPIPE on Claude Code 2.1.x.
$payload = [Console]::In.ReadToEnd()

if ([string]::IsNullOrEmpty($payload)) {
    exit 0
}

try {
    $json = $payload | ConvertFrom-Json
} catch {
    exit 0
}

$exitCode = $null
if ($null -ne $json.tool_response -and ($json.tool_response.PSObject.Properties.Name -contains 'exit_code')) {
    $exitCode = $json.tool_response.exit_code
}

# Only proceed when the tool actually failed. Null or 0 means success.
if ($null -eq $exitCode -or $exitCode -eq 0) {
    exit 0
}

$tool = if ($json.PSObject.Properties.Name -contains 'tool_name' -and $null -ne $json.tool_name) { [string]$json.tool_name } else { 'unknown' }
$stderrText = if ($null -ne $json.tool_response -and ($json.tool_response.PSObject.Properties.Name -contains 'stderr')) { [string]$json.tool_response.stderr } else { '' }

# Generate stable error ID
$datePart = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$hexPart = -join ((48..57) + (97..102) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
$errorId = "RF-$datePart-$hexPart"

# Marker location: per-machine state in LOCALAPPDATA (not OneDrive synced).
$markerDir = Join-Path $env:LOCALAPPDATA 'Claude\plugins\reklam-fabrikasi'
New-Item -ItemType Directory -Path $markerDir -Force | Out-Null

# Truncate stderr safely.
$safeStderr = if ($stderrText.Length -gt 500) {
    ($stderrText.Substring(0, 500)) -replace '"', '\"' -replace "`r", '' -replace "`n", ' '
} else {
    $stderrText -replace '"', '\"' -replace "`r", '' -replace "`n", ' '
}

# Build marker JSON with stable key order.
$marker = [ordered]@{
    timestamp            = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    error_id             = $errorId
    tool                 = $tool
    exit_code            = [int]$exitCode
    stderr_truncated     = $safeStderr
    tier_reached         = 4
    auto_heal_attempted  = $true
    auto_heal_succeeded  = $false
    phase                = 'A'
    note                 = 'Phase B will read this marker to generate structured DM template'
} | ConvertTo-Json -Compress

# Atomic write: tmp then rename.
$tmpPath = Join-Path $markerDir 'last-error.json.tmp'
$finalPath = Join-Path $markerDir 'last-error.json'

$marker | Out-File -FilePath $tmpPath -Encoding UTF8 -NoNewline
Move-Item -Path $tmpPath -Destination $finalPath -Force

exit 0
