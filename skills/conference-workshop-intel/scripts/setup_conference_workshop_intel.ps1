#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$SkillDir = "",
    [string]$Python = "",
    [string[]]$PythonPackages = @(
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "PyYAML>=6.0",
        "openreview-py>=2.0.0",
        "acl-anthology>=1.2.0"
    ),
    [switch]$SkipPythonDeps,
    [switch]$CloneWorkshopTracker,
    [string]$WorkshopTrackerRepo = "https://github.com/Yeping-Hu/ai-workshop-tracker.git",
    [switch]$RunNetworkSmoke,
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

function Resolve-PythonPath {
    param([string]$Requested)

    if ($Requested) {
        return (Resolve-Path -LiteralPath $Requested).Path
    }

    $candidates = @(
        "C:\ProgramData\Anaconda3\envs\gaokao_pg\python.exe",
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "No Python interpreter found. Pass -Python C:\Path\to\python.exe."
}

function Invoke-Logged {
    param(
        [string]$Label,
        [scriptblock]$Action
    )

    Write-Host "== $Label"
    if ($DryRun) {
        return
    }
    & $Action
}

function New-IsolatedVenv {
    param(
        [string]$Root,
        [string]$Name,
        [string]$PythonPath
    )

    $runtime = Join-Path $Root "runtime\$Name"
    $venv = Join-Path $runtime ".venv"
    $venvPy = Join-Path $venv "Scripts\python.exe"

    Invoke-Logged "ensure runtime $Name" {
        New-Item -ItemType Directory -Force -Path $runtime | Out-Null
        if (-not (Test-Path -LiteralPath $venvPy)) {
            & $PythonPath -m venv $venv
        }
    }

    return $venvPy
}

function Install-Packages {
    param(
        [string]$VenvPython,
        [string[]]$Packages
    )

    Invoke-Logged "upgrade pip" {
        & $VenvPython -m pip install --upgrade pip
    }
    Invoke-Logged "install $($Packages -join ', ')" {
        & $VenvPython -m pip install --retries 10 --timeout 120 --no-cache-dir @Packages
    }
}

function Test-PipCheck {
    param([string]$VenvPython)

    Invoke-Logged "pip check" {
        & $VenvPython -m pip check
    }
}

function Ensure-GitRepo {
    param(
        [string]$RepoUrl,
        [string]$Destination
    )

    Invoke-Logged "ensure git repo $RepoUrl" {
        if (Test-Path -LiteralPath (Join-Path $Destination ".git")) {
            & git -C $Destination pull --ff-only
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
            & git clone --depth 1 $RepoUrl $Destination
        }
    }
}

function Test-EnvPresent {
    param([string]$Name)

    $processValue = [Environment]::GetEnvironmentVariable($Name, "Process")
    $userValue = [Environment]::GetEnvironmentVariable($Name, "User")
    return [bool]($processValue -or $userValue)
}

$resolvedSkillDir = Resolve-SkillDir -Requested $SkillDir
$resolvedPython = Resolve-PythonPath -Requested $Python
$privateEnvPath = Join-Path $resolvedSkillDir ".env"
$mainScript = Join-Path $resolvedSkillDir "scripts\conference_workshop_intel.py"
$runtimePython = "skipped"
$workshopTrackerPath = Join-Path $resolvedSkillDir "runtime\source-repos\ai-workshop-tracker"

$summary = [ordered]@{
    skill_dir = $resolvedSkillDir
    python = $resolvedPython
    private_env_path = $privateEnvPath
    python_runtime = "skipped"
    workshop_tracker = "not-cloned"
    dry_run = [bool]$DryRun
    env_present = [ordered]@{
        OPENREVIEW_USERNAME = Test-EnvPresent -Name "OPENREVIEW_USERNAME"
        OPENREVIEW_PASSWORD = Test-EnvPresent -Name "OPENREVIEW_PASSWORD"
        SEMANTIC_SCHOLAR_API_KEY = Test-EnvPresent -Name "SEMANTIC_SCHOLAR_API_KEY"
        GITHUB_TOKEN = Test-EnvPresent -Name "GITHUB_TOKEN"
        HF_TOKEN = Test-EnvPresent -Name "HF_TOKEN"
    }
    public_smoke = "skipped"
}

Invoke-Logged "create private env placeholder" {
    if (-not (Test-Path -LiteralPath $privateEnvPath)) {
        New-Item -ItemType File -Path $privateEnvPath -Force | Out-Null
    }
}

if (-not $SkipPythonDeps) {
    $runtimePython = New-IsolatedVenv -Root $resolvedSkillDir -Name "conference-workshop" -PythonPath $resolvedPython
    Install-Packages -VenvPython $runtimePython -Packages $PythonPackages
    Invoke-Logged "smoke Python imports" {
        & $runtimePython -c "import requests, bs4, yaml, openreview; from acl_anthology import Anthology; print('CONFERENCE_WORKSHOP_IMPORT_OK')"
    }
    Test-PipCheck -VenvPython $runtimePython
    $summary.python_runtime = $runtimePython
}

if ($CloneWorkshopTracker) {
    Ensure-GitRepo -RepoUrl $WorkshopTrackerRepo -Destination $workshopTrackerPath
    if (-not $DryRun) {
        $summary.workshop_tracker = $workshopTrackerPath
    }
}

if ($RunNetworkSmoke) {
    $smokePython = if ($runtimePython -ne "skipped") { $runtimePython } else { $resolvedPython }
    Invoke-Logged "public source smoke" {
        & $smokePython $mainScript public-smoke
    }
    if (-not $DryRun) {
        $summary.public_smoke = "ran"
    }
}

$summary | ConvertTo-Json -Depth 5
