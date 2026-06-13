param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("anysearch", "wechat", "bilibili", "mediacrawler")]
  [string]$Provider,

  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host "[chinese-ai-signal-auth] $Message"
}

function Open-OfficialUrl {
  param([string]$Url)
  Write-Step "Opening setup page: $Url"
  if (-not $DryRun) {
    Start-Process $Url
  }
}

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RepoRoot = Split-Path -Parent (Split-Path -Parent $SkillDir)
$ExternalHelper = Join-Path $RepoRoot "skills\external-api-onboarding\scripts\set_env_secret.ps1"
if (-not (Test-Path $ExternalHelper)) {
  $ExternalHelper = Join-Path $env:USERPROFILE ".codex\skills\external-api-onboarding\scripts\set_env_secret.ps1"
}

$SkillEnvFile = Join-Path $env:USERPROFILE ".codex\skills\chinese-ai-signal-crawler\.env"
$AnySearchEnvFile = Join-Path $env:USERPROFILE ".codex\skills\anysearch\.env"

$Specs = @{
  anysearch = @{
    Url = "https://anysearch.com/console/api-keys"
    EnvFile = $AnySearchEnvFile
    Vars = @("ANYSEARCH_API_KEY")
    Note = "AnySearch can run anonymously with lower limits. Add a key only for higher quota."
  }
  wechat = @{
    Url = "https://github.com/whynpc9/wespy-plus"
    EnvFile = $SkillEnvFile
    Vars = @()
    Note = "For WeChat, prefer known article URLs and wespy-plus. The user must complete any WeChat login, QR scan, CAPTCHA, cookie handling, or local app setup directly in the provider/tool UI."
  }
  bilibili = @{
    Url = "https://github.com/VincentCassano/bilibili-crawler"
    EnvFile = $SkillEnvFile
    Vars = @()
    Note = "For Bilibili, start with small public UID/video metadata captures. Comment capture may require visible login and strict limits."
  }
  mediacrawler = @{
    Url = "https://github.com/NanmiCoder/MediaCrawler"
    EnvFile = $SkillEnvFile
    Vars = @()
    Note = "MediaCrawler setup is optional and platform-login-bound. Use visible user login and small scoped captures only."
  }
}

$Spec = $Specs[$Provider]
Write-Step $Spec.Note
Open-OfficialUrl $Spec.Url

New-Item -ItemType Directory -Force (Split-Path -Parent $Spec.EnvFile) | Out-Null

if ($Spec.Vars.Count -eq 0) {
  Write-Step "No default secret env var is configured for $Provider. Keep cookies/browser state in the external tool's private runtime, not in this repository."
  exit 0
}

if (-not (Test-Path $ExternalHelper)) {
  Write-Step "Secret helper not found. Store values manually in private env file: $($Spec.EnvFile)"
  Write-Step ("Needed env vars: " + ($Spec.Vars -join ", "))
  exit 1
}

foreach ($Name in $Spec.Vars) {
  if ($DryRun) {
    Write-Step "Dry run: would prompt hidden local storage for $Name in $($Spec.EnvFile)"
  } else {
    powershell -ExecutionPolicy Bypass -File $ExternalHelper -EnvFile $Spec.EnvFile -Name $Name
  }
}

Write-Step "Credential setup loop finished. Secret values were not printed."
