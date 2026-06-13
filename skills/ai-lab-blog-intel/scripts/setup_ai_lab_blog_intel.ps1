param(
  [switch]$RunNetworkSmoke
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Script = Join-Path $SkillDir "scripts\ai_lab_blog_intel.py"

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Body
  )
  Write-Host "[ai-lab-blog-intel] $Name"
  & $Body
}

if (-not (Test-Path -LiteralPath $Script)) {
  throw "Missing helper script: $Script"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
  $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
  throw "Python 3 is required for ai-lab-blog-intel."
}

Invoke-Step "Python version" {
  & $python.Source --version
}

Invoke-Step "Schema command" {
  & $python.Source $Script schema | Out-Null
}

Invoke-Step "Plan command" {
  & $python.Source $Script plan --target "frontier AI lab blogs" --org openai --org anthropic --needs posts,links,report | Out-Null
}

if ($RunNetworkSmoke) {
  $SmokeDir = Join-Path ([System.IO.Path]::GetTempPath()) "codex-ai-lab-blog-intel-smoke"
  if (Test-Path -LiteralPath $SmokeDir) {
    Remove-Item -LiteralPath $SmokeDir -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path (Join-Path $SmokeDir "raw") | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $SmokeDir "normalized") | Out-Null

  $FeedOut = Join-Path $SmokeDir "raw\openai_feed.json"
  Invoke-Step "Network smoke: OpenAI RSS feed" {
    & $python.Source $Script fetch-feeds --org openai --max-entries 2 --output $FeedOut | Out-Null
  }

  Invoke-Step "Normalize smoke feed" {
    & $python.Source $Script normalize --input $FeedOut --source feed --output-dir (Join-Path $SmokeDir "normalized") | Out-Null
  }

  $Manifest = Join-Path $SmokeDir "normalized\manifest.normalize.json"
  if (Test-Path -LiteralPath $Manifest) {
    $json = Get-Content -Encoding UTF8 -LiteralPath $Manifest | ConvertFrom-Json
    Write-Host ("[ai-lab-blog-intel] Smoke counts: posts={0}, sources={1}, links={2}" -f $json.counts.posts, $json.counts.sources, $json.counts.links)
  }
}

Write-Host "[ai-lab-blog-intel] Setup check complete."
