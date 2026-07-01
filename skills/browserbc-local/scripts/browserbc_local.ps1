param(
    [Parameter(Position = 0)]
    [ValidateSet("status", "start", "build-extension", "verify")]
    [string]$Command = "status"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = "D:\agent-workflow-lab\harnesses\browser-bc"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$ExtensionDir = Join-Path $Root "extension\dist\chrome-mv3"
$Port = 8099
$Url = "http://127.0.0.1:$Port/"
$DefaultHeaders = @{ Authorization = "Bearer jfl-local-dev-key" }

function Test-Root {
    if (-not (Test-Path -LiteralPath $Root)) {
        throw "BrowserBC checkout not found: $Root"
    }
    if (-not (Test-Path -LiteralPath $Python)) {
        throw "BrowserBC Python venv not found: $Python"
    }
}

function Get-Listener {
    Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Listen" } |
        Select-Object -First 1
}

function Get-ServerStatus {
    $listener = Get-Listener
    $rootStatus = $null
    $config = $null
    $ext = $null
    if ($listener) {
        try {
            $rootStatus = (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5).StatusCode
            $config = (Invoke-WebRequest -Uri ($Url + "api/config") -Headers $DefaultHeaders -UseBasicParsing -TimeoutSec 5).Content | ConvertFrom-Json
            $ext = (Invoke-WebRequest -Uri ($Url + "api/ext") -Headers $DefaultHeaders -UseBasicParsing -TimeoutSec 5).Content | ConvertFrom-Json
        } catch {
            $rootStatus = "error: $($_.Exception.Message)"
        }
    }
    [pscustomobject]@{
        Root = $Root
        Url = $Url
        Listening = [bool]$listener
        OwningProcess = if ($listener) { $listener.OwningProcess } else { $null }
        RootStatus = $rootStatus
        LlmKeySet = if ($config) { $config.llm_key_set } else { $null }
        ExtensionBuilt = if ($ext) { $ext.built } else { Test-Path -LiteralPath (Join-Path $ExtensionDir "manifest.json") }
        ExtensionDir = $ExtensionDir
    }
}

function Start-BrowserBc {
    Test-Root
    $listener = Get-Listener
    if ($listener) {
        Get-ServerStatus
        return
    }
    Start-Process -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "server.server:app", "--host", "127.0.0.1", "--port", "$Port", "--log-level", "warning") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 3
    Get-ServerStatus
}

function Build-Extension {
    Test-Root
    Push-Location (Join-Path $Root "extension")
    try {
        npx --yes pnpm@11.9.0 install
        npx --yes pnpm@11.9.0 approve-builds --all
        npx --yes pnpm@11.9.0 run typecheck
        npx --yes pnpm@11.9.0 run build
    } finally {
        Pop-Location
    }
    Get-ServerStatus
}

function Invoke-Verify {
    Test-Root
    Push-Location $Root
    try {
        & $Python -c "import server.server; print('server import ok')"
        & $Python -m harness.main --help | Select-Object -First 8
    } finally {
        Pop-Location
    }
    Get-ServerStatus
}

switch ($Command) {
    "status" { Get-ServerStatus | Format-List }
    "start" { Start-BrowserBc | Format-List }
    "build-extension" { Build-Extension | Format-List }
    "verify" { Invoke-Verify | Format-List }
}
