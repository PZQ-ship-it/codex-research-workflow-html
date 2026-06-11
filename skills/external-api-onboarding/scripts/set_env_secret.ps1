param(
    [Parameter(Mandatory = $true)]
    [string]$EnvFile,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z_][A-Za-z0-9_]*$')]
    [string]$Name,

    [string]$Value = "",

    [ValidateSet("bare", "double-quoted")]
    [string]$Format = "bare",

    [switch]$AllowPlainValue,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[external-api-onboarding] $Message"
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

function Format-EnvLine {
    param(
        [string]$Key,
        [string]$Secret,
        [string]$LineFormat
    )

    if ($Secret -match "[`r`n]") {
        throw "Secret values with newlines are not supported by this helper."
    }

    if ($LineFormat -eq "double-quoted") {
        $escaped = $Secret.Replace('\', '\\').Replace('"', '\"')
        return "$Key=""$escaped"""
    }

    return "$Key=$Secret"
}

function Set-EnvFileValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Secret,
        [string]$LineFormat
    )

    $dir = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = Get-Content -LiteralPath $Path -Encoding UTF8
    }

    $newLine = Format-EnvLine -Key $Key -Secret $Secret -LineFormat $LineFormat
    $found = $false
    $pattern = "^\s*$([regex]::Escape($Key))\s*="

    $updated = foreach ($line in $lines) {
        if ($line -match $pattern) {
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

$resolvedEnvFile = $EnvFile
$parent = Split-Path -Parent $resolvedEnvFile
if (-not [string]::IsNullOrWhiteSpace($parent) -and (Test-Path -LiteralPath $parent)) {
    $resolvedParent = (Resolve-Path -LiteralPath $parent).Path
    $resolvedEnvFile = Join-Path $resolvedParent (Split-Path -Leaf $resolvedEnvFile)
}

Write-Info "Target file: $resolvedEnvFile"
Write-Info "Target variable: $Name"

$existing = $false
if (Test-Path -LiteralPath $resolvedEnvFile) {
    $existing = Select-String -LiteralPath $resolvedEnvFile -Pattern "^\s*$([regex]::Escape($Name))\s*=" -Quiet
}

if ($DryRun) {
    $action = if ($existing) { "update" } else { "create" }
    Write-Info "Dry run only: would $action $Name without printing its value."
    exit 0
}

if ($existing -and -not $Force) {
    Write-Info "$Name already exists in the target .env."
    $answer = Read-Host "Overwrite it? Type YES to continue"
    if ($answer -ne "YES") {
        Write-Info "Cancelled without changing the existing value."
        exit 0
    }
}

$secure = $null
$plain = $null

try {
    if (-not [string]::IsNullOrWhiteSpace($Value)) {
        if (-not $AllowPlainValue) {
            throw "Refusing command-line -Value without -AllowPlainValue. Prefer hidden prompt for real secrets."
        }
        $plain = $Value
        Write-Info "Using command-line value because -AllowPlainValue was set. Do not use this mode for real secrets unless you accept shell-history risk."
    } else {
        $secure = Read-Host "Enter $Name (input hidden)" -AsSecureString
        $plain = ConvertTo-PlainText -Secure $secure
    }

    if ([string]::IsNullOrWhiteSpace($plain)) {
        throw "$Name cannot be empty."
    }

    Set-EnvFileValue -Path $resolvedEnvFile -Key $Name -Secret $plain -LineFormat $Format
    Write-Info "Saved $Name to .env without printing its value."
    Write-Info "Restart Codex or the affected MCP/server process if it already loaded environment variables."
} finally {
    $plain = $null
    if ($null -ne $secure) {
        $secure.Dispose()
    }
}
