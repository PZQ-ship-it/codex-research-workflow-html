param(
    [string]$EnvFile = "$env:USERPROFILE\.codex\skills\dianping-explore\.env",
    [string]$ProviderUrl = "https://www.dianping.com/"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$externalHelper = "$env:USERPROFILE\.codex\skills\external-api-onboarding\scripts\set_env_secret.ps1"
if (-not (Test-Path -LiteralPath $externalHelper)) {
    throw "external-api-onboarding helper not found: $externalHelper"
}

Write-Host "[dianping-explore] Opening Dianping in your browser."
Write-Host "[dianping-explore] Complete login or verification there, then copy the Cookie string from your browser DevTools."
Write-Host "[dianping-explore] Paste it only into the hidden prompt that follows. It will not be printed."
Start-Process $ProviderUrl | Out-Null

powershell -ExecutionPolicy Bypass -File $externalHelper `
    -EnvFile $EnvFile `
    -Name DIANPING_COOKIE `
    -Format double-quoted
