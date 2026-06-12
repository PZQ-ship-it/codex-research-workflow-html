#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$SkillDir = "",
    [string]$Python = "",
    [string[]]$PythonPackages = @(
        "huggingface_hub>=0.34.0",
        "datasets>=2.20.0",
        "openml>=0.15.0",
        "kaggle>=1.6.0",
        "kagglehub>=0.3.0",
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "pyarrow>=15.0.0"
    ),
    [switch]$SkipPythonDeps,
    [switch]$RegisterGitHubMcp,
    [switch]$RegisterHuggingFaceMcp,
    [switch]$RegisterKaggleMcp,
    [string]$GitHubMcpUrl = "https://api.githubcopilot.com/mcp/",
    [string]$GitHubBearerTokenEnvVar = "GITHUB_PAT_TOKEN",
    [string]$HuggingFaceMcpUrl = "https://huggingface.co/mcp",
    [string]$KaggleMcpUrl = "https://www.kaggle.com/mcp",
    [switch]$CloneBenchmarkRepos,
    [string[]]$BenchmarkRepo = @(),
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

    $globalSkill = Join-Path $env:USERPROFILE ".codex\skills\code-model-benchmark-intel"
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

function Test-McpRegistered {
    param([string]$Name)

    $list = & codex mcp list 2>$null
    return [bool]($list | Select-String -SimpleMatch $Name)
}

function Test-EnvPresent {
    param([string]$Name)

    $processValue = [Environment]::GetEnvironmentVariable($Name, "Process")
    $userValue = [Environment]::GetEnvironmentVariable($Name, "User")
    return [bool]($processValue -or $userValue)
}

function Add-RemoteMcpConfigIfMissing {
    param(
        [string]$Name,
        [string]$Url,
        [string]$BearerTokenEnvVar = ""
    )

    Invoke-Logged "configure remote MCP $Name" {
        if (Test-McpRegistered -Name $Name) {
            Write-Host "$Name already registered"
            return
        }

        $configDir = Join-Path $env:USERPROFILE ".codex"
        $configPath = Join-Path $configDir "config.toml"
        New-Item -ItemType Directory -Force -Path $configDir | Out-Null
        if (-not (Test-Path -LiteralPath $configPath)) {
            New-Item -ItemType File -Path $configPath -Force | Out-Null
        }

        $lines = @(Get-Content -LiteralPath $configPath -Encoding UTF8)
        if ($lines | Select-String -Pattern "^\s*\[mcp_servers\.$([regex]::Escape($Name))\]\s*$" -Quiet) {
            Write-Host "$Name already present in config"
            return
        }

        $block = @(
            "",
            "[mcp_servers.$Name]",
            "url = `"$Url`""
        )
        if (-not [string]::IsNullOrWhiteSpace($BearerTokenEnvVar)) {
            $block += "bearer_token_env_var = `"$BearerTokenEnvVar`""
        }
        Set-Content -LiteralPath $configPath -Value (@($lines) + $block) -Encoding UTF8
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

$benchmarkRepos = [ordered]@{
    swebench = "https://github.com/SWE-bench/SWE-bench.git"
    livebench = "https://github.com/livebench/livebench.git"
    livecodebench = "https://github.com/livecodebench/livecodebench.git"
    bigcodebench = "https://github.com/bigcode-project/bigcodebench.git"
}

$resolvedSkillDir = Resolve-SkillDir -Requested $SkillDir
$resolvedPython = Resolve-PythonPath -Requested $Python
$privateEnvPath = Join-Path $resolvedSkillDir ".env"

$summary = [ordered]@{
    skill_dir = $resolvedSkillDir
    python = $resolvedPython
    private_env_path = $privateEnvPath
    python_runtime = "skipped"
    dry_run = [bool]$DryRun
    github_mcp_registered = Test-McpRegistered -Name "github"
    huggingface_mcp_registered = Test-McpRegistered -Name "huggingface"
    kaggle_mcp_registered = Test-McpRegistered -Name "kaggle"
    planned_actions = @()
    env_present = [ordered]@{
        GITHUB_PAT_TOKEN = Test-EnvPresent -Name "GITHUB_PAT_TOKEN"
        HF_TOKEN = Test-EnvPresent -Name "HF_TOKEN"
        HUGGING_FACE_HUB_TOKEN = Test-EnvPresent -Name "HUGGING_FACE_HUB_TOKEN"
        KAGGLE_USERNAME = Test-EnvPresent -Name "KAGGLE_USERNAME"
        KAGGLE_KEY = Test-EnvPresent -Name "KAGGLE_KEY"
        OPENML_API_KEY = Test-EnvPresent -Name "OPENML_API_KEY"
    }
    cloned_benchmark_repos = @()
}

Invoke-Logged "create private env placeholder" {
    if (-not (Test-Path -LiteralPath $privateEnvPath)) {
        New-Item -ItemType File -Path $privateEnvPath -Force | Out-Null
    }
}

if (-not $SkipPythonDeps) {
    $runtimePython = New-IsolatedVenv -Root $resolvedSkillDir -Name "code-model-benchmark" -PythonPath $resolvedPython
    Install-Packages -VenvPython $runtimePython -Packages $PythonPackages
    Invoke-Logged "smoke Python imports" {
        & $runtimePython -c "import importlib.util; import huggingface_hub, datasets, openml, kagglehub, requests, pandas, pyarrow; assert importlib.util.find_spec('kaggle'); print('CODE_MODEL_BENCHMARK_IMPORT_OK')"
    }
    if ($RunNetworkSmoke) {
        Invoke-Logged "smoke Hugging Face public API" {
            & $runtimePython -c "from huggingface_hub import HfApi; info=HfApi().model_info('distilbert/distilbert-base-uncased'); print({'HF_PUBLIC_API_OK': True, 'model_id': info.modelId})"
        }
        Invoke-Logged "smoke OpenML public metadata" {
            & $runtimePython -c "import openml; ds=openml.datasets.get_dataset(61, download_data=False); print({'OPENML_PUBLIC_METADATA_OK': True, 'dataset_id': ds.dataset_id, 'name': ds.name})"
        }
    }
    Test-PipCheck -VenvPython $runtimePython
    $summary.python_runtime = $runtimePython
}

if ($RegisterGitHubMcp) {
    $summary.planned_actions += "register GitHub MCP"
    Add-RemoteMcpConfigIfMissing -Name "github" -Url $GitHubMcpUrl -BearerTokenEnvVar $GitHubBearerTokenEnvVar
    if (-not $DryRun) {
        $summary.github_mcp_registered = Test-McpRegistered -Name "github"
    }
}

if ($RegisterHuggingFaceMcp) {
    $summary.planned_actions += "register Hugging Face MCP"
    Add-RemoteMcpConfigIfMissing -Name "huggingface" -Url $HuggingFaceMcpUrl
    if (-not $DryRun) {
        $summary.huggingface_mcp_registered = Test-McpRegistered -Name "huggingface"
    }
}

if ($RegisterKaggleMcp) {
    $summary.planned_actions += "register Kaggle MCP"
    Add-RemoteMcpConfigIfMissing -Name "kaggle" -Url $KaggleMcpUrl
    if (-not $DryRun) {
        $summary.kaggle_mcp_registered = Test-McpRegistered -Name "kaggle"
    }
}

if ($CloneBenchmarkRepos) {
    $requestedRepos = $BenchmarkRepo
    if (-not $requestedRepos -or $requestedRepos.Count -eq 0) {
        $requestedRepos = @("swebench", "livebench", "livecodebench", "bigcodebench")
    }

    $repoRoot = Join-Path $resolvedSkillDir "runtime\benchmark-repos"
    foreach ($repoName in $requestedRepos) {
        $normalizedName = $repoName.ToLowerInvariant()
        if (-not $benchmarkRepos.Contains($normalizedName)) {
            throw "Unknown benchmark repo '$repoName'. Known names: $($benchmarkRepos.Keys -join ', ')"
        }
        $destination = Join-Path $repoRoot $normalizedName
        $summary.planned_actions += "clone benchmark repo $normalizedName"
        Ensure-GitRepo -RepoUrl $benchmarkRepos[$normalizedName] -Destination $destination
        if (-not $DryRun) {
            $summary.cloned_benchmark_repos += $destination
        }
    }
}

$summary | ConvertTo-Json -Depth 5
