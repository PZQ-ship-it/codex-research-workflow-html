param(
    [string]$EnvFile = "$env:USERPROFILE\.codex\skills\dianping-explore\.env",
    [string]$ProviderUrl = "https://www.dianping.com/",
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
    "--url", $ProviderUrl
)

if ($DryRun) {
    $argsList += "--dry-run"
}

& $python @argsList
