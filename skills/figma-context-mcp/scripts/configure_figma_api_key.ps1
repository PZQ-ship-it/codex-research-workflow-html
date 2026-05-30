param(
    [string]$RepoSkillDir = "",
    [string]$GlobalSkillDir = "",
    [string]$ApiKey = "",
    [switch]$SkipMcpUpdate,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[figma-context-mcp] $Message"
}

function ConvertTo-PlainText {
    param([System.Security.SecureString]$Secure)
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

function Set-EnvFileValue {
    param(
        [string]$Path,
        [string]$Name,
        [string]$Value
    )

    $dir = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $dir | Out-Null

    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = Get-Content -LiteralPath $Path -Encoding UTF8
    }

    $escaped = $Value.Replace('\', '\\').Replace('"', '\"')
    $newLine = "$Name=""$escaped"""
    $found = $false
    $updated = foreach ($line in $lines) {
        if ($line -match "^\s*$([regex]::Escape($Name))\s*=") {
            $found = $true
            $newLine
        } else {
            $line
        }
    }

    if (-not $found) {
        $updated = @($updated) + $newLine
    }

    Set-Content -LiteralPath $Path -Value $updated -Encoding UTF8
}

function Copy-SkillWithoutSecrets {
    param(
        [string]$Source,
        [string]$Destination
    )

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Get-ChildItem -LiteralPath $Source -Force | Where-Object {
        $_.Name -notin @(".env", "__pycache__")
    } | ForEach-Object {
        $target = Join-Path $Destination $_.Name
        if ($_.PSIsContainer) {
            if (Test-Path -LiteralPath $target) {
                Remove-Item -LiteralPath $target -Recurse -Force
            }
            Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
        } else {
            Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        }
    }
}

if ([string]::IsNullOrWhiteSpace($RepoSkillDir)) {
    $RepoSkillDir = Split-Path -Parent $PSScriptRoot
}
$RepoSkillDir = (Resolve-Path -LiteralPath $RepoSkillDir).Path

if ([string]::IsNullOrWhiteSpace($GlobalSkillDir)) {
    $GlobalSkillDir = Join-Path $env:USERPROFILE ".codex\skills\figma-context-mcp"
}

Write-Info "Repo skill: $RepoSkillDir"
Write-Info "Global skill: $GlobalSkillDir"

$existingEnv = Join-Path $GlobalSkillDir ".env"
if ((Test-Path -LiteralPath $existingEnv) -and -not $Force) {
    $hasExisting = Select-String -LiteralPath $existingEnv -Pattern "^\s*FIGMA_API_KEY\s*=" -Quiet
    if ($hasExisting) {
        Write-Info "A FIGMA_API_KEY entry already exists in the global skill .env."
        $answer = Read-Host "Overwrite it? Type YES to continue"
        if ($answer -ne "YES") {
            Write-Info "Cancelled without changing the existing key."
            exit 0
        }
    }
}

$secure = $null
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $secure = Read-Host "Enter FIGMA_API_KEY (input hidden)" -AsSecureString
    $plain = ConvertTo-PlainText -Secure $secure
} else {
    $plain = $ApiKey
    Write-Info "Using FIGMA_API_KEY from -ApiKey parameter for non-interactive setup."
}
try {
    if ([string]::IsNullOrWhiteSpace($plain)) {
        throw "FIGMA_API_KEY cannot be empty."
    }

    Copy-SkillWithoutSecrets -Source $RepoSkillDir -Destination $GlobalSkillDir
    Set-EnvFileValue -Path $existingEnv -Name "FIGMA_API_KEY" -Value $plain

    Write-Info "Wrote FIGMA_API_KEY to global skill .env without printing it."
    Write-Info "Path: $existingEnv"

    if (-not $SkipMcpUpdate) {
        $imageDir = Join-Path (Split-Path -Parent (Split-Path -Parent $RepoSkillDir)) "generated_assets\figma"
        New-Item -ItemType Directory -Force -Path $imageDir | Out-Null

        $codex = Get-Command codex -ErrorAction SilentlyContinue
        if ($null -eq $codex) {
            Write-Info "codex command not found; skipped MCP update."
        } else {
            $null = & codex mcp remove figma_context 2>$null
            & codex mcp add figma_context -- cmd /c npx -y figma-developer-mcp --env $existingEnv --stdio --image-dir $imageDir --format yaml | Out-Host
            Write-Info "Updated figma_context MCP to load the global skill .env."
        }
    }

    Write-Info "Done. Restart Codex so newly launched MCP processes can load the updated key."
} finally {
    if ($null -ne $plain) {
        $plain = $null
    }
    if ($null -ne $secure) {
        $secure.Dispose()
    }
}
