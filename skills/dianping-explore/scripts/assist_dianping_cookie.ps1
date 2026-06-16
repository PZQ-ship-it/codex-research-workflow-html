param(
    [string]$EnvFile = "$env:USERPROFILE\.codex\skills\dianping-explore\.env",
    [string]$ProviderUrl = "https://www.dianping.com/",
    [int]$TimeoutSeconds = 600,
    [switch]$Headless,
    [switch]$AllowUnverifiedSave,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $ScriptDir "cli.py"
$Helper = Join-Path $ScriptDir "assist_dianping_cookie.py"

$statusJson = python $Cli status | ConvertFrom-Json
$python = $statusJson.status.venv_python
if ([string]::IsNullOrWhiteSpace($python) -or -not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$argsList = @(
    $Helper,
    "--env-file", $EnvFile,
    "--url", $ProviderUrl,
    "--timeout-seconds", $TimeoutSeconds
)

if ($Headless) {
    $argsList += "--headless"
}

if ($AllowUnverifiedSave) {
    $argsList += "--allow-unverified-save"
}

if ($DryRun) {
    $argsList += "--dry-run"
}

& $python @argsList
