#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$SkillDir = "",
    [string]$Python = "",
    [string]$OpenReviewPyPackage = "openreview-py==2.2.2",
    [string]$AclAnthologyPackage = "acl-anthology==1.2.0",
    [switch]$SkipOpenReviewPy,
    [switch]$SkipAclAnthology,
    [switch]$InstallPaperSearchMcp,
    [switch]$RegisterPaperSearchMcp,
    [switch]$AllowOptionalRestrictedConnectors,
    [string]$OpenReviewKnowledgeMcpUrl = "",
    [switch]$RegisterOpenReviewKnowledgeMcp,
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

    $globalSkill = Join-Path $env:USERPROFILE ".codex\skills\paper-review-source-intel"
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

$resolvedSkillDir = Resolve-SkillDir -Requested $SkillDir
$resolvedPython = Resolve-PythonPath -Requested $Python
$summary = [ordered]@{
    skill_dir = $resolvedSkillDir
    python = $resolvedPython
    openreview_py = "skipped"
    acl_anthology = "skipped"
    openreview_knowledge_mcp_registered = $false
    paper_search_mcp = "not-installed"
    paper_search_mcp_registered = $false
}

if (-not $SkipOpenReviewPy) {
    $openreviewPython = New-IsolatedVenv -Root $resolvedSkillDir -Name "openreview-py" -PythonPath $resolvedPython
    Install-Packages -VenvPython $openreviewPython -Packages @($OpenReviewPyPackage)
    Invoke-Logged "smoke openreview-py import" {
        & $openreviewPython -c "import openreview; print('OPENREVIEW_IMPORT_OK')"
    }
    if ($RunNetworkSmoke) {
        Invoke-Logged "smoke OpenReview public API" {
            & $openreviewPython -c "import json, openreview; c=openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net'); g=c.get_group('ICLR.cc/2025/Conference'); print(json.dumps({'OPENREVIEW_PUBLIC_API_OK': True, 'group_id': g.id}, ensure_ascii=False))"
        }
    }
    Test-PipCheck -VenvPython $openreviewPython
    $summary.openreview_py = $openreviewPython
}

if (-not $SkipAclAnthology) {
    $aclPython = New-IsolatedVenv -Root $resolvedSkillDir -Name "acl-anthology" -PythonPath $resolvedPython
    Install-Packages -VenvPython $aclPython -Packages @($AclAnthologyPackage, "typing_extensions>=4.0")
    Invoke-Logged "smoke acl-anthology import" {
        & $aclPython -c "from acl_anthology import Anthology; print('ACL_ANTHOLOGY_IMPORT_OK')"
    }
    Test-PipCheck -VenvPython $aclPython
    $summary.acl_anthology = $aclPython
}

if ($InstallPaperSearchMcp -or $RegisterPaperSearchMcp) {
    $paperSearchPython = New-IsolatedVenv -Root $resolvedSkillDir -Name "paper-search-mcp" -PythonPath $resolvedPython
    Install-Packages -VenvPython $paperSearchPython -Packages @("paper-search-mcp")
    Invoke-Logged "smoke paper-search-mcp import" {
        & $paperSearchPython -c "import paper_search_mcp; print('PAPER_SEARCH_MCP_IMPORT_OK')"
    }
    Test-PipCheck -VenvPython $paperSearchPython
    $summary.paper_search_mcp = $paperSearchPython

    if ($RegisterPaperSearchMcp) {
        if (-not $AllowOptionalRestrictedConnectors) {
            throw "Refusing to register paper-search-mcp without -AllowOptionalRestrictedConnectors. Read references/full-setup.md first; keep Sci-Hub, proxies, paid connectors, and private keys disabled unless explicitly authorized."
        }
        $envPath = Join-Path $resolvedSkillDir ".env"
        Invoke-Logged "create private env placeholder" {
            if (-not (Test-Path -LiteralPath $envPath)) {
                New-Item -ItemType File -Path $envPath -Force | Out-Null
            }
        }
        Invoke-Logged "register paper_search_mcp in Codex" {
            & codex mcp add paper_search_mcp --env "PAPER_SEARCH_MCP_ENV_FILE=$envPath" -- $paperSearchPython -m paper_search_mcp.server
        }
        $summary.paper_search_mcp_registered = $true
    }
}

if ($RegisterOpenReviewKnowledgeMcp) {
    if (-not $OpenReviewKnowledgeMcpUrl) {
        throw "Pass -OpenReviewKnowledgeMcpUrl http://localhost:<port>/mcp after starting the official openreview/openreview-mcp server."
    }
    Invoke-Logged "register openreview_knowledge MCP" {
        & codex mcp add openreview_knowledge --url $OpenReviewKnowledgeMcpUrl
    }
    $summary.openreview_knowledge_mcp_registered = $true
}

$summary | ConvertTo-Json -Depth 5
