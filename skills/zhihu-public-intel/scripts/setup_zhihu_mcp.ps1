param(
    [string]$RepoUrl = "https://github.com/alizeeblack-code/zhihu-mcp.git",
    [string]$RuntimeRoot = "",
    [string]$PythonPath = "",
    [string]$McpName = "zhihu_mcp",
    [switch]$SkipMcpUpdate,
    [switch]$SkipPlaywrightInstall,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[zhihu-public-intel] $Message"
}

function Get-PythonVersion {
    param([string]$Python)
    $code = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    (& $Python -c $code).Trim()
}

function Assert-Python310 {
    param([string]$Python)
    $code = "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    & $Python -c $code
    if ($LASTEXITCODE -ne 0) {
        $version = Get-PythonVersion -Python $Python
        throw "Python 3.10+ is required for zhihu-mcp; got $version from $Python"
    }
}

if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) {
    $RuntimeRoot = Join-Path $env:USERPROFILE ".codex\skills\zhihu-public-intel\runtime"
}
$RuntimeRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RuntimeRoot)
$CheckoutDir = Join-Path $RuntimeRoot "zhihu-mcp"

if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCmd) {
        throw "python was not found. Pass -PythonPath with a Python 3.10+ interpreter."
    }
    $PythonPath = $pythonCmd.Source
}
$PythonPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($PythonPath)

Write-Info "Runtime root: $RuntimeRoot"
Write-Info "Checkout dir: $CheckoutDir"
Write-Info "Python: $PythonPath"

Assert-Python310 -Python $PythonPath

New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null

if (Test-Path -LiteralPath $CheckoutDir) {
    if (-not (Test-Path -LiteralPath (Join-Path $CheckoutDir ".git"))) {
        throw "Checkout dir exists but is not a git repository: $CheckoutDir"
    }
    Write-Info "Updating existing zhihu-mcp checkout."
    git -C $CheckoutDir fetch --depth 1 origin | Out-Host
    git -C $CheckoutDir pull --ff-only | Out-Host
} else {
    Write-Info "Cloning zhihu-mcp."
    git clone --depth 1 $RepoUrl $CheckoutDir | Out-Host
}

$VenvDir = Join-Path $CheckoutDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if ((-not (Test-Path -LiteralPath $VenvPython)) -or $Force) {
    Write-Info "Creating virtual environment."
    & $PythonPath -m venv $VenvDir
}

Write-Info "Installing Python dependencies."
& $VenvPython -m pip install --upgrade pip | Out-Host
& $VenvPython -m pip install -r (Join-Path $CheckoutDir "requirements.txt") | Out-Host

if (-not $SkipPlaywrightInstall) {
    Write-Info "Installing Playwright Chromium."
    & $VenvPython -m playwright install chromium | Out-Host
}

$ConfigPath = Join-Path $CheckoutDir "config.json"
$config = [ordered]@{
    browser = [ordered]@{
        headless = $true
        viewport = [ordered]@{
            width = 1920
            height = 1080
        }
        user_data_dir = "./zhihu-profile"
        stealth_level = "advanced"
        chrome_cookie_extraction = $false
        use_pinchtab = $false
        pinchtab_url = "http://127.0.0.1:9877"
        pinchtab_profile = "zhihu"
    }
    cookies_path = "cookies.json"
}
$configJson = $config | ConvertTo-Json -Depth 6
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ConfigPath, $configJson + [Environment]::NewLine, $utf8NoBom)
Write-Info "Wrote safe config with chrome_cookie_extraction=false: $ConfigPath"

Push-Location $CheckoutDir
try {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    $env:ZHIHU_MCP_CONFIG = $ConfigPath
    & $VenvPython -c "import mcp_server; from zhihu_mcp.config import load_config; cfg=load_config(); print('IMPORT_OK'); print('chrome_cookie_extraction=' + str(cfg.browser.chrome_cookie_extraction).lower())" | Out-Host
} finally {
    Remove-Item Env:\PYTHONUTF8 -ErrorAction SilentlyContinue
    Remove-Item Env:\PYTHONIOENCODING -ErrorAction SilentlyContinue
    Remove-Item Env:\ZHIHU_MCP_CONFIG -ErrorAction SilentlyContinue
    Pop-Location
}

if (-not $SkipMcpUpdate) {
    $codex = Get-Command codex -ErrorAction SilentlyContinue
    if ($null -eq $codex) {
        Write-Info "codex command not found; skipped MCP registration."
    } else {
        $ServerScript = Join-Path $CheckoutDir "mcp_server.py"
        $null = & codex mcp remove $McpName 2>$null
        & codex mcp add `
            --env HEADLESS=true `
            --env ZHIHU_MCP_CONFIG=$ConfigPath `
            --env PYTHONUTF8=1 `
            --env PYTHONIOENCODING=utf-8 `
            $McpName -- $VenvPython $ServerScript | Out-Host
        Write-Info "Registered Codex MCP server: $McpName"
    }
}

Write-Info "Done. Restart Codex so the newly registered MCP server can be loaded by the running session."
Write-Info "No real cookies were copied or extracted. Add an authorized local cookies.json only if logged-in Zhihu access is required."
