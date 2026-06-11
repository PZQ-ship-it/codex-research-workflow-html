param(
    [string]$RuntimeRoot = "",
    [int]$TimeoutSeconds = 180,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[zhihu-login] $Message"
}

if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) {
    $RuntimeRoot = Join-Path $env:USERPROFILE ".codex\skills\zhihu-public-intel\runtime"
}

$RuntimeRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RuntimeRoot)
$CheckoutDir = Join-Path $RuntimeRoot "zhihu-mcp"
$VenvPython = Join-Path $CheckoutDir ".venv\Scripts\python.exe"
$CookiesPath = Join-Path $CheckoutDir "cookies.json"
$ProfileDir = Join-Path $CheckoutDir "zhihu-profile"
$McpServer = Join-Path $CheckoutDir "mcp_server.py"

$status = [ordered]@{
    runtime_root = $RuntimeRoot
    checkout_dir = $CheckoutDir
    venv_python = $VenvPython
    mcp_server = $McpServer
    cookies_path = $CookiesPath
    profile_dir = $ProfileDir
    checkout_exists = Test-Path -LiteralPath $CheckoutDir
    venv_python_exists = Test-Path -LiteralPath $VenvPython
    mcp_server_exists = Test-Path -LiteralPath $McpServer
    cookies_file_exists = Test-Path -LiteralPath $CookiesPath
    timeout_seconds = $TimeoutSeconds
    force = [bool]$Force
}

if ($DryRun) {
    $status | ConvertTo-Json -Depth 4
    exit 0
}

if (-not (Test-Path -LiteralPath $CheckoutDir)) {
    throw "zhihu-mcp runtime is missing. Run scripts\setup_zhihu_mcp.ps1 first."
}
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "zhihu-mcp virtual environment is missing. Run scripts\setup_zhihu_mcp.ps1 first."
}
if (-not (Test-Path -LiteralPath $McpServer)) {
    throw "mcp_server.py is missing under runtime checkout: $McpServer"
}
if ((Test-Path -LiteralPath $CookiesPath) -and (-not $Force)) {
    throw "cookies.json already exists. Re-run with -Force only if you want to refresh it."
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

Write-Info "Opening a visible Chromium window for Zhihu login."
Write-Info "Complete login/MFA/CAPTCHA in the browser. Cookie values will not be printed."
Write-Info "Private cookie target: $CookiesPath"

$env:ZHIHU_COOKIES_PATH = $CookiesPath
$env:ZHIHU_PROFILE_DIR = $ProfileDir
$env:ZHIHU_LOGIN_TIMEOUT = [string]$TimeoutSeconds
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$pythonCode = @'
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright


async def main() -> int:
    cookies_path = Path(os.environ["ZHIHU_COOKIES_PATH"])
    profile_dir = Path(os.environ["ZHIHU_PROFILE_DIR"])
    timeout = int(os.environ.get("ZHIHU_LOGIN_TIMEOUT", "180"))
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.zhihu.com/signin?next=%2F", wait_until="domcontentloaded", timeout=60000)

        deadline = time.monotonic() + timeout
        logged_in = False
        last_cookie_count = 0
        while time.monotonic() < deadline:
            cookies = await context.cookies(["https://www.zhihu.com", "https://zhuanlan.zhihu.com"])
            last_cookie_count = len(cookies)
            names = {cookie.get("name") for cookie in cookies}
            if {"z_c0", "d_c0"}.issubset(names):
                logged_in = True
                break
            await page.wait_for_timeout(2000)

        if not logged_in:
            await context.close()
            print(json.dumps({
                "status": "login_not_confirmed",
                "reason": "auth cookies were not detected before timeout",
                "cookie_count_seen": last_cookie_count,
            }, ensure_ascii=False, indent=2))
            return 2

        cookies = await context.cookies(["https://www.zhihu.com", "https://zhuanlan.zhihu.com"])
        zhihu_cookies = [cookie for cookie in cookies if "zhihu" in cookie.get("domain", "")]
        cookies_path.write_text(json.dumps(zhihu_cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        await context.close()
        print(json.dumps({
            "status": "ok",
            "cookies_path": str(cookies_path),
            "cookie_count": len(zhihu_cookies),
            "auth_cookie_names_present": True,
            "secret_values_printed": False,
        }, ensure_ascii=False, indent=2))
        return 0


raise SystemExit(asyncio.run(main()))
'@

try {
    $pythonCode | & $VenvPython -
    if ($LASTEXITCODE -ne 0) {
        throw "Visible login helper failed with exit code $LASTEXITCODE."
    }
} finally {
    Remove-Item Env:\ZHIHU_COOKIES_PATH -ErrorAction SilentlyContinue
    Remove-Item Env:\ZHIHU_PROFILE_DIR -ErrorAction SilentlyContinue
    Remove-Item Env:\ZHIHU_LOGIN_TIMEOUT -ErrorAction SilentlyContinue
    Remove-Item Env:\PYTHONUTF8 -ErrorAction SilentlyContinue
    Remove-Item Env:\PYTHONIOENCODING -ErrorAction SilentlyContinue
}

Write-Info "Done. Restart Codex if zhihu_mcp was newly registered, then run check_login_status or cookie_status."
