param()

$ErrorActionPreference = "Stop"

function Write-Json($Object) {
    $Object | ConvertTo-Json -Depth 8 -Compress
}

function Get-RepoRoot($Cwd) {
    if ([string]::IsNullOrWhiteSpace($Cwd)) {
        $Cwd = (Get-Location).Path
    }
    try {
        $root = (& git -C $Cwd rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0 -and $root) {
            return (Resolve-Path -LiteralPath $root).Path
        }
    }
    catch {
    }
    return (Resolve-Path -LiteralPath $Cwd).Path
}

function Get-ArtifactFiles($RepoRoot, [string]$Pattern) {
    $pathPattern = $Pattern.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $parent = Split-Path -Parent $pathPattern
    $leaf = Split-Path -Leaf $pathPattern
    $searchRoot = if ([string]::IsNullOrWhiteSpace($parent)) {
        $RepoRoot
    }
    else {
        Join-Path $RepoRoot $parent
    }
    if (-not (Test-Path -LiteralPath $searchRoot)) {
        return @()
    }
    return @(Get-ChildItem -LiteralPath $searchRoot -Filter $leaf -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending)
}

function Test-ConfirmedArtifact($RepoRoot, [string[]]$Patterns, [string[]]$AcceptedStatuses) {
    foreach ($pattern in $Patterns) {
        $files = Get-ArtifactFiles $RepoRoot $pattern

        foreach ($file in $files) {
            $text = [string](Get-Content -Raw -LiteralPath $file.FullName -ErrorAction SilentlyContinue)
            $text = $text.TrimStart([char]0xFEFF)
            foreach ($status in $AcceptedStatuses) {
                $escapedStatus = [regex]::Escape($status)
                if ($text -match "(?im)^\s*(stage_status|status)\s*:\s*$escapedStatus\s*$") {
                    return $true
                }
            }
        }
    }
    return $false
}

function Test-ArtifactKeyValue($RepoRoot, [string[]]$Patterns, [string]$Key, [string[]]$AcceptedValues) {
    foreach ($pattern in $Patterns) {
        $files = Get-ArtifactFiles $RepoRoot $pattern

        foreach ($file in $files) {
            $text = [string](Get-Content -Raw -LiteralPath $file.FullName -ErrorAction SilentlyContinue)
            $text = $text.TrimStart([char]0xFEFF)
            foreach ($value in $AcceptedValues) {
                $escapedKey = [regex]::Escape($Key)
                $escapedValue = [regex]::Escape($value)
                if ($text -match "(?im)^\s*$escapedKey\s*:\s*$escapedValue\s*$") {
                    return $true
                }
            }
        }
    }
    return $false
}

function Deny($Reason) {
    Write-Json @{
        hookSpecificOutput = @{
            hookEventName = "PreToolUse"
            permissionDecision = "deny"
            permissionDecisionReason = $Reason
        }
    }
    exit 0
}

function Get-ToolText($Event) {
    $parts = @()
    if ($Event.tool_name) { $parts += [string]$Event.tool_name }
    if ($Event.tool_input) {
        if ($Event.tool_input.command) { $parts += [string]$Event.tool_input.command }
        $parts += ($Event.tool_input | ConvertTo-Json -Depth 20 -Compress)
    }
    return ($parts -join "`n")
}

function Test-WriteIntent($ToolText) {
    if ($ToolText -match "(?i)\b(apply_patch|Set-Content|Add-Content|Out-File|New-Item|Copy-Item|Move-Item|Remove-Item|python|python3|py|pptx|SaveAs|Export|write_text|open\(.+[`"'][wa]\b|>\s*[\w\.\\/])") {
        return $true
    }
    return $false
}

function Get-TargetStage($ToolText) {
    $normalized = $ToolText.Replace('\', '/')
    if ($normalized -match '(?i)align/(material_inventory|material_manifest|fact_ledger|claim_source_map)_v.*\.(md|csv|json)') {
        return "material_fact_ledger"
    }
    if ($normalized -match '(?i)align/PPT_storyboard_v.*\.md') {
        return "storyboard"
    }
    if ($normalized -match '(?i)align/(template_inventory|template_layout_map|PPT_asset_audit|PPT_asset_manifest|visual_enrichment_plan|ppt_layout_plan)_v.*\.(md|csv|json)') {
        return "asset_layout_plan"
    }
    if ($normalized -match '(?i)align/academic_figure_prompt_v.*\.md') {
        return "academic_figure_prompt"
    }
    if ($normalized -match '(?i)(generated_pptx_test/|align/ppt_deck_build_manifest_v.*\.md|\.pptx\b)') {
        return "deck_build"
    }
    if ($normalized -match '(?i)(qa/rendered_pages/|qa/deck_render\.pdf|qa/ppt_render_qa_v.*\.md|deck_render\.pdf)') {
        return "render_qa"
    }
    return $null
}

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    exit 0
}

$event = $raw | ConvertFrom-Json
$cwd = if ($event.cwd) { [string]$event.cwd } else { (Get-Location).Path }
$repoRoot = Get-RepoRoot $cwd
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    $repoRoot = (Resolve-Path -LiteralPath ".").Path
}
$eventName = [string]$event.hook_event_name

if ($eventName -eq "UserPromptSubmit") {
    $prompt = [string]$event.prompt
    if ($prompt -match '(?i)(manuscript-to-ppt|ppt-|PPT|slide|deck|答辩|幻灯|阶段|确认)') {
        Write-Json @{
            hookSpecificOutput = @{
                hookEventName = "UserPromptSubmit"
                additionalContext = "PPT workflow policy: every stage must stop after producing a draft artifact. Continue only after the user explicitly confirms/freeze the prior stage artifact with stage_status: confirmed. Do not auto-advance across stages."
            }
        }
    }
    exit 0
}

if ($eventName -ne "PreToolUse") {
    exit 0
}

$toolText = Get-ToolText $event
if (-not (Test-WriteIntent $toolText)) {
    exit 0
}

$targetStage = Get-TargetStage $toolText
if (-not $targetStage) {
    exit 0
}

$hasBrief = Test-ConfirmedArtifact $repoRoot @("align/ppt_production_brief_v*.md") @("confirmed")
$hasFacts = Test-ConfirmedArtifact $repoRoot @("align/fact_ledger_v*.md") @("confirmed")
$hasStoryboard = Test-ConfirmedArtifact $repoRoot @("align/PPT_storyboard_v*.md") @("confirmed")
$hasAssetPlan = Test-ConfirmedArtifact $repoRoot @("align/PPT_asset_audit_v*.md", "align/visual_enrichment_plan_v*.md") @("confirmed")
$hasAcademicFigurePrompt = Test-ConfirmedArtifact $repoRoot @("align/academic_figure_prompt_v*.md") @("confirmed")
$hasDeckBuild = Test-ConfirmedArtifact $repoRoot @("align/ppt_deck_build_manifest_v*.md") @("confirmed")
$requiresAcademicFigurePrompt = Test-ArtifactKeyValue $repoRoot @("align/visual_enrichment_plan_v*.md") "requires_academic_figure_prompt" @("true", "yes")

switch ($targetStage) {
    "material_fact_ledger" {
        if (-not $hasBrief) {
            Deny "PPT stage gate blocked material/fact output: no confirmed align/ppt_production_brief_v*.md. Stop and confirm the production brief first."
        }
    }
    "storyboard" {
        if (-not ($hasBrief -and $hasFacts)) {
            Deny "PPT stage gate blocked storyboard output: confirmed production brief and fact ledger are required first."
        }
    }
    "asset_layout_plan" {
        if (-not ($hasBrief -and $hasFacts -and $hasStoryboard)) {
            Deny "PPT stage gate blocked asset/layout output: confirmed brief, fact ledger, and storyboard are required first."
        }
    }
    "academic_figure_prompt" {
        if (-not ($hasBrief -and $hasFacts -and $hasStoryboard -and $hasAssetPlan)) {
            Deny "PPT stage gate blocked academic figure prompt output: confirmed brief, fact ledger, storyboard, and asset/layout plan are required first."
        }
    }
    "deck_build" {
        if (-not ($hasBrief -and $hasFacts -and $hasStoryboard -and $hasAssetPlan)) {
            Deny "PPT stage gate blocked PPTX/deck output: confirmed brief, fact ledger, storyboard, and asset/layout plan are required first."
        }
        if ($requiresAcademicFigurePrompt -and -not $hasAcademicFigurePrompt) {
            Deny "PPT stage gate blocked PPTX/deck output: visual enrichment plan requires a confirmed academic figure prompt first."
        }
    }
    "render_qa" {
        if (-not $hasDeckBuild) {
            Deny "PPT stage gate blocked render QA output: confirmed deck build manifest is required first."
        }
    }
}
