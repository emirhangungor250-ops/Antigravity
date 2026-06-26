# Reklam Fabrikası em dash and en dash stripper, Windows variant.
#
# This script reads JSON from stdin per the Claude Code hooks contract.
# Claude Code 2.1.x sends a single JSON object on stdin to every hook.
# For PostToolUse on Write or Edit, the payload contains tool_input.file_path.
#
# The CLAUDE_TOOL_FILE_PATH env var does not exist on Claude Code 2.1.x.
# The fallback below only fires if stdin is empty, which would mean the
# host runtime reverted to env-var dispatch. Treat the fallback as defensive
# and unreliable, not as a supported path.

$ErrorActionPreference = 'SilentlyContinue'

# Read full payload first so stdin is fully drained on every code path.
# Failing to drain stdin causes EPIPE on Claude Code 2.1.x.
$payload = [Console]::In.ReadToEnd()

$target = $null

if (-not [string]::IsNullOrEmpty($payload)) {
    try {
        $json = $payload | ConvertFrom-Json
        if ($null -ne $json.tool_input -and ($json.tool_input.PSObject.Properties.Name -contains 'file_path')) {
            $target = [string]$json.tool_input.file_path
        }
    } catch { }
}

# Defensive fallback to the legacy env var. Unreliable on Claude Code 2.1.x.
if ([string]::IsNullOrEmpty($target)) {
    $target = $env:CLAUDE_TOOL_FILE_PATH
}

if ([string]::IsNullOrEmpty($target) -or -not (Test-Path -LiteralPath $target -PathType Leaf)) {
    exit 0
}

# Skip binary files and large media.
$ext = [System.IO.Path]::GetExtension($target).ToLowerInvariant()
$skip = @('.png', '.jpg', '.jpeg', '.mp4', '.webp', '.gif', '.zip', '.pdf')
if ($skip -contains $ext) {
    exit 0
}

# Read full file as UTF8, replace em dash (U+2014) and en dash (U+2013) with ", ".
try {
    $content = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)
} catch {
    exit 0
}

$emDash = [char]0x2014
$enDash = [char]0x2013
$replaced = $content.Replace([string]$emDash, ', ').Replace([string]$enDash, ', ')

if ($replaced -ne $content) {
    # Write back UTF8 without BOM to preserve repository encoding.
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($target, $replaced, $utf8NoBom)
}

exit 0
