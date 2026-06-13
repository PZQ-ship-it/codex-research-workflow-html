param(
  [switch]$RunNetworkSmoke,
  [switch]$InstallOptionalPythonRuntime,
  [string]$PythonExe = "python",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host "[early-signal-intel] $Message"
}

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ScriptPath = Join-Path $SkillDir "scripts\early_signal_intel.py"
$GlobalSkillDir = Join-Path $env:USERPROFILE ".codex\skills\early-signal-intel"
$EnvFile = Join-Path $GlobalSkillDir ".env"
$RuntimeDir = Join-Path $GlobalSkillDir "runtime\python"
$VenvDir = Join-Path $RuntimeDir ".venv"

function Get-PythonVersionParts {
  param([string]$Executable)
  $versionText = (& $Executable -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null)
  if (-not $versionText) { return $null }
  $parts = $versionText.Trim().Split(".")
  return [pscustomobject]@{
    Text = $versionText.Trim()
    Major = [int]$parts[0]
    Minor = [int]$parts[1]
    Patch = [int]$parts[2]
  }
}

function Find-OptionalPython {
  param([string]$Preferred)
  $candidates = New-Object System.Collections.Generic.List[string]
  $candidates.Add($Preferred)
  $condaEnvRoot = Join-Path $env:ProgramData "Anaconda3\envs"
  if (Test-Path $condaEnvRoot) {
    Get-ChildItem -LiteralPath $condaEnvRoot -Directory | ForEach-Object {
      $py = Join-Path $_.FullName "python.exe"
      if (Test-Path $py) { $candidates.Add($py) }
    }
  }
  foreach ($candidate in $candidates) {
    $version = Get-PythonVersionParts $candidate
    if ($null -ne $version -and $version.Major -eq 3 -and $version.Minor -ge 10) {
      return [pscustomobject]@{ Path = $candidate; Version = $version }
    }
  }
  return $null
}

Write-Step "Skill directory: $SkillDir"
Write-Step "Private env target: $EnvFile"

if ($DryRun) {
  Write-Step "Dry run requested; no directories or runtimes will be created."
} else {
  New-Item -ItemType Directory -Force $GlobalSkillDir | Out-Null
}

Write-Step "Checking Python CLI."
& $PythonExe --version
& $PythonExe $ScriptPath schema | Out-Null
Write-Step "Schema command passed."

if ($InstallOptionalPythonRuntime) {
  $optionalPython = Find-OptionalPython $PythonExe
  if ($null -eq $optionalPython) {
    throw "Optional provider runtime requires Python >= 3.10. Install or pass -PythonExe <path-to-python-3.10+>. alphaXiv SDK additionally needs Python >= 3.12."
  }
  if ($DryRun) {
    Write-Step "Would create optional runtime at $VenvDir using $($optionalPython.Path) ($($optionalPython.Version.Text))."
    Write-Step "Would install atproto, praw, feedparser. Would install alphaxiv-py only with Python >= 3.12."
  } else {
    Write-Step "Creating optional runtime with $($optionalPython.Path) ($($optionalPython.Version.Text))."
    New-Item -ItemType Directory -Force $RuntimeDir | Out-Null
    if (-not (Test-Path $VenvDir)) {
      & $optionalPython.Path -m venv $VenvDir
    }
    $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install atproto praw feedparser
    $venvVersion = Get-PythonVersionParts $VenvPython
    if ($venvVersion.Major -eq 3 -and $venvVersion.Minor -ge 12) {
      & $VenvPython -m pip install alphaxiv-py
      Write-Step "Installed alphaxiv-py."
    } else {
      Write-Step "Skipped alphaxiv-py because it currently requires Python >= 3.12; this runtime is $($venvVersion.Text)."
    }
    Write-Step "Optional Python runtime installed."
  }
}

if ($RunNetworkSmoke) {
  Write-Step "Running no-key HN smoke test."
  & $PythonExe $ScriptPath fetch-hn --query "alphaXiv arXiv discussion" --max-results 2 | Out-Null
  Write-Step "HN smoke test passed."

  Write-Step "Running RSS smoke test."
  & $PythonExe $ScriptPath fetch-rss --feed "https://openai.com/news/rss.xml" --max-entries 2 | Out-Null
  Write-Step "RSS smoke test passed."
}

Write-Step "Done. Optional credentials, if needed, belong in $EnvFile."
