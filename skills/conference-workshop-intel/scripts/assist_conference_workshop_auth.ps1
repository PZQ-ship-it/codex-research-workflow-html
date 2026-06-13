#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$SkillDir = "",
    [string[]]$Provider = @("openreview"),
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-SkillDir {
    param([string]$Requested)

    if ($Requested) {
        return (Resolve-Path -LiteralPath $Requested).Path
    }

    $globalSkill = Join-Path $env:USERPROFILE ".codex\skills\conference-workshop-intel"
    if (Test-Path -LiteralPath $globalSkill) {
        return (Resolve-Path -LiteralPath $globalSkill).Path
    }

    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

function Open-ProviderPage {
    param([string]$Url)

    if ($DryRun) {
        return
    }
    Start-Process -FilePath $Url
}

$resolvedSkillDir = Resolve-SkillDir -Requested $SkillDir
$envFile = Join-Path $resolvedSkillDir ".env"
$secretHelper = Join-Path $env:USERPROFILE ".codex\skills\external-api-onboarding\scripts\set_env_secret.ps1"

if (-not $DryRun -and -not (Test-Path -LiteralPath $envFile)) {
    New-Item -ItemType File -Path $envFile -Force | Out-Null
}

$providerInfo = @{
    "openreview" = @{
        url = "https://openreview.net/login"
        env = @("OPENREVIEW_USERNAME", "OPENREVIEW_PASSWORD")
        note = "Only for user-authorized visibility; never use credentials to bypass private reviews or venue controls."
    }
    "semantic-scholar" = @{
        url = "https://www.semanticscholar.org/product/api"
        env = @("SEMANTIC_SCHOLAR_API_KEY")
        note = "Optional enrichment and higher rate limits; public enrichment should be attempted first."
    }
    "github" = @{
        url = "https://github.com/settings/personal-access-tokens/new"
        env = @("GITHUB_TOKEN")
        note = "Optional higher GitHub API limits or private authorized repositories; prefer read-only, fine-grained, expiring tokens."
    }
    "huggingface" = @{
        url = "https://huggingface.co/settings/tokens"
        env = @("HF_TOKEN")
        note = "Optional only when a selected public-source route needs higher HF limits or authorized datasets."
    }
    "paper-search" = @{
        url = "https://github.com/openags/paper-search-mcp"
        env = @("PAPER_SEARCH_MCP_UNPAYWALL_EMAIL", "PAPER_SEARCH_MCP_CORE_API_KEY", "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY")
        note = "Optional if routing through paper-search MCP for enrichment; keep all secrets private."
    }
}

$results = @()
$expandedProviders = @()
foreach ($rawProvider in $Provider) {
    $expandedProviders += ($rawProvider -split "," | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })
}

foreach ($name in $expandedProviders) {
    if (-not $providerInfo.ContainsKey($name)) {
        throw "Unknown provider '$name'. Known providers: $($providerInfo.Keys -join ', ')"
    }
    $info = $providerInfo[$name]
    Open-ProviderPage -Url $info.url
    $commands = @()
    foreach ($envName in $info.env) {
        $commands += "powershell -ExecutionPolicy Bypass -File `"$secretHelper`" -EnvFile `"$envFile`" -Name $envName"
    }
    $results += [ordered]@{
        provider = $name
        opened_url = $info.url
        env_file = $envFile
        env_var_names = $info.env
        storage_commands = $commands
        note = $info.note
        dry_run = [bool]$DryRun
    }
}

$results | ConvertTo-Json -Depth 5
