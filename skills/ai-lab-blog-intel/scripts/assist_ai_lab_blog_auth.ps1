param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("anysearch", "apify", "github", "huggingface")]
  [string]$Provider,

  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$UserSkillDir = Join-Path $env:USERPROFILE ".codex\skills\ai-lab-blog-intel"
$PrivateEnv = Join-Path $UserSkillDir ".env"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $SkillDir)
$ExternalWriter = Join-Path $RepoRoot "skills\external-api-onboarding\scripts\set_env_secret.ps1"

if (-not (Test-Path -LiteralPath $ExternalWriter)) {
  $ExternalWriter = Join-Path $env:USERPROFILE ".codex\skills\external-api-onboarding\scripts\set_env_secret.ps1"
}

$providerInfo = @{
  anysearch = @{
    EnvName = "ANYSEARCH_API_KEY"
    Console = "https://anysearch.com/console/api-keys"
    Notes = "Optional. Anonymous AnySearch works with lower limits; use a key only for higher quota live discovery."
  }
  apify = @{
    EnvName = "APIFY_TOKEN"
    Console = "https://console.apify.com/account/integrations"
    Notes = "Optional paid/managed crawler fallback. Ask before starting any paid actor run."
  }
  github = @{
    EnvName = "GITHUB_TOKEN"
    Console = "https://github.com/settings/tokens"
    Notes = "Optional read-only enrichment for open-source crawler/feed repositories."
  }
  huggingface = @{
    EnvName = "HF_TOKEN"
    Console = "https://huggingface.co/settings/tokens"
    Notes = "Optional read-only enrichment for linked model or dataset cards."
  }
}

$info = $providerInfo[$Provider]
Write-Host "[ai-lab-blog-intel] Provider: $Provider"
Write-Host "[ai-lab-blog-intel] Env var: $($info.EnvName)"
Write-Host "[ai-lab-blog-intel] Private env file: $PrivateEnv"
Write-Host "[ai-lab-blog-intel] $($info.Notes)"

if ($DryRun) {
  Write-Host "[ai-lab-blog-intel] Dry run only; no browser or file write."
  exit 0
}

New-Item -ItemType Directory -Force -Path $UserSkillDir | Out-Null

Write-Host "[ai-lab-blog-intel] Opening official provider page. Complete login/key creation yourself; do not paste secrets into chat."
Start-Process $info.Console -WindowStyle Hidden

if (-not (Test-Path -LiteralPath $ExternalWriter)) {
  throw "Missing external-api-onboarding secret writer: $ExternalWriter"
}

Write-Host "[ai-lab-blog-intel] When ready, paste the secret into the hidden local prompt."
powershell -ExecutionPolicy Bypass -File $ExternalWriter -EnvFile $PrivateEnv -Name $info.EnvName

Write-Host "[ai-lab-blog-intel] Stored status only: secret writer completed for $($info.EnvName). Secret value was not printed."
