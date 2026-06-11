#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$SkillDir = "",
    [string]$Python = "",
    [string]$OpenReviewPyPackage = "openreview-py==2.2.2",
    [string]$AclAnthologyPackage = "acl-anthology==1.2.0",
    [string]$ScholarlyPackage = "scholarly",
    [string]$OpenReviewMcpRepo = "https://github.com/openreview/openreview-mcp.git",
    [switch]$SkipOpenReviewPy,
    [switch]$SkipAclAnthology,
    [switch]$SkipScholarly,
    [switch]$InstallPaperSearchMcp,
    [switch]$RegisterPaperSearchMcp,
    [switch]$InstallOpenReviewKnowledgeMcp,
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

    $globalSkill = Join-Path $env:USERPROFILE ".codex\skills\google-scholar-profile-intel"
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

$resolvedSkillDir = Resolve-SkillDir -Requested $SkillDir
$resolvedPython = Resolve-PythonPath -Requested $Python
$summary = [ordered]@{
    skill_dir = $resolvedSkillDir
    python = $resolvedPython
    openreview_py = "skipped"
    acl_anthology = "skipped"
    scholarly = "skipped"
    paper_search_mcp = "not-installed"
    paper_search_mcp_registered = Test-McpRegistered -Name "paper_search_mcp"
    openreview_knowledge_mcp = "not-installed"
    openreview_knowledge_mcp_registered = Test-McpRegistered -Name "openreview_knowledge"
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

if (-not $SkipScholarly) {
    $scholarlyPython = New-IsolatedVenv -Root $resolvedSkillDir -Name "scholarly" -PythonPath $resolvedPython
    Install-Packages -VenvPython $scholarlyPython -Packages @($ScholarlyPackage)
    Invoke-Logged "smoke scholarly import" {
        & $scholarlyPython -c "from scholarly import scholarly; print('SCHOLARLY_IMPORT_OK')"
    }
    Test-PipCheck -VenvPython $scholarlyPython
    $summary.scholarly = $scholarlyPython
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
        $envPath = Join-Path $resolvedSkillDir ".env"
        $downloadsPath = Join-Path $resolvedSkillDir "runtime\paper-search-mcp\downloads"
        Invoke-Logged "create private env placeholder" {
            if (-not (Test-Path -LiteralPath $envPath)) {
                New-Item -ItemType File -Path $envPath -Force | Out-Null
            }
            New-Item -ItemType Directory -Force -Path $downloadsPath | Out-Null
        }
        Invoke-Logged "register paper_search_mcp in Codex" {
            if (Test-McpRegistered -Name "paper_search_mcp") {
                Write-Host "paper_search_mcp already registered"
            } else {
                & codex mcp add paper_search_mcp `
                    --env "PAPER_SEARCH_MCP_ENV_FILE=$envPath" `
                    --env "PAPER_SEARCH_MCP_DOWNLOADS=$downloadsPath" `
                    -- $paperSearchPython -m paper_search_mcp.server
            }
        }
        $summary.paper_search_mcp_registered = $true
    }
}

if ($InstallOpenReviewKnowledgeMcp -or ($RegisterOpenReviewKnowledgeMcp -and -not $OpenReviewKnowledgeMcpUrl)) {
    $mcpSrc = Join-Path $resolvedSkillDir "runtime\openreview-mcp-src"
    Ensure-GitRepo -RepoUrl $OpenReviewMcpRepo -Destination $mcpSrc
    $mcpPython = New-IsolatedVenv -Root $resolvedSkillDir -Name "openreview-mcp" -PythonPath $resolvedPython
    Install-Packages -VenvPython $mcpPython -Packages @($mcpSrc)
    Invoke-Logged "smoke openreview-mcp import" {
        & $mcpPython -c "import openreview_mcp; print('OPENREVIEW_MCP_IMPORT_OK')"
    }
    Test-PipCheck -VenvPython $mcpPython
    $summary.openreview_knowledge_mcp = Join-Path (Split-Path -Parent $mcpPython) "openreview-mcp.exe"
}

if ($RegisterOpenReviewKnowledgeMcp) {
    if ($OpenReviewKnowledgeMcpUrl) {
        Invoke-Logged "register openreview_knowledge HTTP MCP" {
            if (Test-McpRegistered -Name "openreview_knowledge") {
                Write-Host "openreview_knowledge already registered"
            } else {
                & codex mcp add openreview_knowledge --url $OpenReviewKnowledgeMcpUrl
            }
        }
    } else {
        $mcpExe = $summary.openreview_knowledge_mcp
        if ($mcpExe -eq "not-installed") {
            $mcpExe = Join-Path $resolvedSkillDir "runtime\openreview-mcp\.venv\Scripts\openreview-mcp.exe"
        }
        if ((-not $DryRun) -and (-not (Test-Path -LiteralPath $mcpExe))) {
            throw "OpenReview knowledge MCP executable not found. Re-run with -InstallOpenReviewKnowledgeMcp or pass -OpenReviewKnowledgeMcpUrl."
        }
        Invoke-Logged "register openreview_knowledge stdio MCP" {
            if (Test-McpRegistered -Name "openreview_knowledge") {
                Write-Host "openreview_knowledge already registered"
            } else {
                & codex mcp add openreview_knowledge -- $mcpExe --transport stdio
            }
        }
    }
    $summary.openreview_knowledge_mcp_registered = $true
}

$summary | ConvertTo-Json -Depth 5
