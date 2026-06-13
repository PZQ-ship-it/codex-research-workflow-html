param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("alphaxiv", "reddit", "bluesky", "x")]
  [string]$Provider,

  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host "[early-signal-auth] $Message"
}

function Open-OfficialUrl {
  param([string]$Url)
  Write-Step "Opening official setup page: $Url"
  if (-not $DryRun) {
    Start-Process -WindowStyle Hidden $Url
  }
}

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RepoRoot = Split-Path -Parent (Split-Path -Parent $SkillDir)
$ExternalHelper = Join-Path $RepoRoot "skills\external-api-onboarding\scripts\set_env_secret.ps1"
if (-not (Test-Path $ExternalHelper)) {
  $ExternalHelper = Join-Path $env:USERPROFILE ".codex\skills\external-api-onboarding\scripts\set_env_secret.ps1"
}

$EnvFile = Join-Path $env:USERPROFILE ".codex\skills\early-signal-intel\.env"
New-Item -ItemType Directory -Force (Split-Path -Parent $EnvFile) | Out-Null

$Specs = @{
  alphaxiv = @{
    Url = "https://alphaxiv.org"
    Vars = @("ALPHAXIV_API_KEY")
    Note = "alphaXiv public reads can often work without a key. Add a key only for authenticated or higher-quota workflows."
  }
  reddit = @{
    Url = "https://www.reddit.com/prefs/apps"
    Vars = @("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT")
    Note = "Use a narrow read-only script app and comply with Reddit Data API Terms. Do not use Reddit data for model training."
  }
  bluesky = @{
    Url = "https://bsky.app/settings/app-passwords"
    Vars = @("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD")
    Note = "Use an app password, not the account password. Public Jetstream/RSS-like routes may not need auth."
  }
  x = @{
    Url = "https://developer.x.com/en/portal/dashboard"
    Vars = @("X_BEARER_TOKEN")
    Note = "Official X API may cost money. Ask before real paid requests; unofficial login scrapers are not configured by this helper."
  }
}

$Spec = $Specs[$Provider]
Write-Step $Spec.Note
Open-OfficialUrl $Spec.Url

if (-not (Test-Path $ExternalHelper)) {
  Write-Step "Secret helper not found. Store values manually in private env file: $EnvFile"
  Write-Step ("Needed env vars: " + ($Spec.Vars -join ", "))
  exit 1
}

foreach ($Name in $Spec.Vars) {
  if ($Name -eq "REDDIT_USER_AGENT" -or $Name -eq "BLUESKY_HANDLE") {
    Write-Step "Optional non-secret metadata env var: $Name. Use hidden helper only if you want it stored with the secret set."
  }
  if ($DryRun) {
    Write-Step "Dry run: would prompt hidden local storage for $Name in $EnvFile"
  } else {
    powershell -ExecutionPolicy Bypass -File $ExternalHelper -EnvFile $EnvFile -Name $Name
  }
}

Write-Step "Credential setup loop finished. Secret values were not printed. Smoke-test with the provider-specific route before bulk collection."
