param(
  [switch]$RunNetworkSmoke,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

function Write-Step {
  param([string]$Message)
  Write-Host "[chinese-ai-signal-crawler] $Message"
}

function Invoke-Checked {
  param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
  )
  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
  }
}

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ScriptPath = Join-Path $SkillDir "scripts\chinese_ai_signal_crawler.py"
$GlobalSkillDir = Join-Path $env:USERPROFILE ".codex\skills\chinese-ai-signal-crawler"
$EnvFile = Join-Path $GlobalSkillDir ".env"
$AnySearchCli = Join-Path $env:USERPROFILE ".codex\skills\anysearch\scripts\anysearch_cli.py"

Write-Step "Skill directory: $SkillDir"
Write-Step "Private env target: $EnvFile"

if ($DryRun) {
  Write-Step "Dry run requested; no directories will be created."
} else {
  New-Item -ItemType Directory -Force $GlobalSkillDir | Out-Null
}

Write-Step "Checking Python CLI."
Invoke-Checked python --version
Invoke-Checked python $ScriptPath schema | Out-Null
Invoke-Checked python $ScriptPath plan --target "中文AI圈 diffusion" --needs media,anysearch,report | Out-Null
Write-Step "Schema and plan commands passed."

if (Test-Path $AnySearchCli) {
  Write-Step "Checking AnySearch doc command."
  Invoke-Checked python $AnySearchCli doc | Out-Null
  Write-Step "AnySearch CLI is available."
} else {
  Write-Step "AnySearch CLI not found at $AnySearchCli. Discovery can still use public pages/RSS; configure/sync AnySearch for search."
}

if ($RunNetworkSmoke) {
  Write-Step "Running public page smoke test."
  Invoke-Checked python $ScriptPath fetch-page --url "https://www.qbitai.com/" --max-links 5 | Out-Null
  Write-Step "Public page smoke test passed."

  if (Test-Path $AnySearchCli) {
    Write-Step "Running tiny AnySearch smoke test."
    Invoke-Checked python $ScriptPath fetch-anysearch --query "机器之心 量子位 新智元 PaperWeekly AI" --max-results 2 | Out-Null
    Write-Step "AnySearch smoke test passed."
  }
}

Write-Step "Done. Optional provider secrets belong in private user-level env files only."
