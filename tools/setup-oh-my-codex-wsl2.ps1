param(
  [string]$DistroName = "Ubuntu-24.04",
  [string]$LinuxUser = "codex",
  [switch]$SkipOmxSetup
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host "[omx-wsl2] $Message"
}

function Convert-ToWslPath {
  param([string]$Path)

  $resolved = Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue
  if ($resolved) {
    $Path = $resolved.ProviderPath
  }

  if ($Path -match "^([A-Za-z]):\\(.*)$") {
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2] -replace "\\", "/"
    return "/mnt/$drive/$rest"
  }

  return "."
}

function Show-ManualConfigurationGuide {
  param(
    [string]$DistroName,
    [string]$ProjectWslPath
  )

  Write-Host ""
  Write-Host "Manual configuration guide"
  Write-Host "=========================="
  Write-Host "1. Open the WSL distro:"
  Write-Host "   wsl -d $DistroName"
  Write-Host ""
  Write-Host "2. Authenticate Codex inside WSL. Do this manually; do not copy Windows auth.json:"
  Write-Host "   codex login"
  Write-Host "   codex login status"
  Write-Host ""
  Write-Host "3. If you use a custom provider, proxy, or MCP tokens, configure them inside WSL manually:"
  Write-Host "   - review ~/.codex/config.toml"
  Write-Host "   - set required environment variables in ~/.bashrc or another WSL-local shell profile"
  Write-Host "   - keep API keys, tokens, and passwords out of scripts and repo files"
  Write-Host ""
  Write-Host "4. Optional: sync non-sensitive Windows global Codex guidance into WSL:"
  Write-Host "   .\tools\sync-codex-global-to-wsl.ps1"
  Write-Host ""
  Write-Host "5. Verify from the project path:"
  Write-Host "   cd `"$ProjectWslPath`""
  Write-Host "   omx doctor"
  Write-Host "   omx exec --skip-git-repo-check -C `"$ProjectWslPath`" `"Reply with exactly OMX-EXEC-OK`""
  Write-Host ""
  Write-Host "6. If WSL reports an old kernel later, update it from Windows when network access is stable:"
  Write-Host "   wsl --update"
}

function Test-IsAdmin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = [Security.Principal.WindowsPrincipal]::new($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Enable-FeatureIfNeeded {
  param([string]$FeatureName)

  $feature = Get-WindowsOptionalFeature -Online -FeatureName $FeatureName
  if ($feature.State -ne "Enabled") {
    Write-Step "Enabling Windows feature: $FeatureName"
    Enable-WindowsOptionalFeature -Online -FeatureName $FeatureName -All -NoRestart | Out-Null
  }
}

function Get-WslDistros {
  try {
    return (& wsl.exe -l -q 2>$null) |
      ForEach-Object { ($_ -replace "`0", "").Trim() } |
      Where-Object { $_ }
  } catch {
    return @()
  }
}

if (-not (Test-IsAdmin)) {
  throw "Run this script from an elevated PowerShell session."
}

Write-Step "Preparing Windows WSL2 prerequisites"
Enable-FeatureIfNeeded -FeatureName "Microsoft-Windows-Subsystem-Linux"
Enable-FeatureIfNeeded -FeatureName "VirtualMachinePlatform"
& bcdedit /set hypervisorlaunchtype auto | Out-Null

$lxssManager = Get-Service -Name LxssManager -ErrorAction SilentlyContinue
if (-not $lxssManager) {
  Write-Warning "LxssManager is not registered yet. Restart Windows, then rerun this script."
  exit 3010
}

Write-Step "Ensuring Ubuntu 24.04 app package is installed"
$ubuntuPackage = Get-AppxPackage -Name CanonicalGroupLimited.Ubuntu24.04LTS -ErrorAction SilentlyContinue
if (-not $ubuntuPackage) {
  winget install -e --id Canonical.Ubuntu.2404 --source winget --accept-package-agreements --accept-source-agreements
}

Write-Step "Setting WSL default version to 2 when supported"
& wsl.exe --set-default-version 2
if ($LASTEXITCODE -ne 0) {
  Write-Warning "wsl --set-default-version 2 failed. Continuing; older inbox WSL may still allow distro conversion after initialization."
}

$distros = @(Get-WslDistros)
if ($distros -notcontains $DistroName) {
  Write-Step "Initializing $DistroName as root"
  $ubuntuLauncher = Get-Command ubuntu2404.exe -ErrorAction SilentlyContinue
  if ($ubuntuLauncher) {
    & $ubuntuLauncher.Source install --root
    if ($LASTEXITCODE -ne 0) {
      & $ubuntuLauncher.Source run true
    }
  } else {
    & wsl.exe --install -d $DistroName --no-launch
  }
}

$distros = @(Get-WslDistros)
$activeDistro = if ($distros -contains $DistroName) {
  $DistroName
} else {
  $distros | Where-Object { $_ -like "Ubuntu*" } | Select-Object -First 1
}

if (-not $activeDistro) {
  throw "Ubuntu is not visible to wsl.exe yet. Restart Windows and rerun this script."
}

Write-Step "Converting $activeDistro to WSL2 when supported"
& wsl.exe --set-version $activeDistro 2
if ($LASTEXITCODE -ne 0) {
  Write-Warning "Could not force WSL2 conversion. Check 'wsl -l -v' after the script finishes."
}

Write-Step "Installing Linux packages, Node.js 20, Codex CLI, and oh-my-codex"
$linuxBootstrap = @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

linux_user='__LINUX_USER__'

if ! id -u "$linux_user" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$linux_user"
fi
usermod -aG sudo "$linux_user"
printf '%s ALL=(ALL) NOPASSWD:ALL\n' "$linux_user" >/etc/sudoers.d/90-codex
chmod 0440 /etc/sudoers.d/90-codex

apt-get update
apt-get install -y ca-certificates curl gnupg git tmux build-essential cargo rustc

node_major=0
if command -v node >/dev/null 2>&1; then
  node_major=$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)
fi

if [ "$node_major" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

npm install -g @openai/codex
npm install -g oh-my-codex

printf '[user]\ndefault=%s\n' "$linux_user" >/etc/wsl.conf
'@

$linuxBootstrap = $linuxBootstrap.Replace("__LINUX_USER__", $LinuxUser)

$encodedBootstrap = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($linuxBootstrap))
& wsl.exe -d $activeDistro -u root -- bash -lc "echo '$encodedBootstrap' | base64 -d >/tmp/omx-bootstrap.sh && bash /tmp/omx-bootstrap.sh"

Write-Step "Restarting $activeDistro so the default user takes effect"
& wsl.exe --terminate $activeDistro

if (-not $SkipOmxSetup) {
  Write-Step "Running omx setup for Linux user '$LinuxUser'"
  & wsl.exe -d $activeDistro -- bash -lc "omx setup --scope user --merge-agents || omx setup"
}

Write-Step "Version smoke test"
& wsl.exe -d $activeDistro -- bash -lc "set -e; node -v; npm -v; codex --version; omx --version; tmux -V"

Write-Step "omx doctor"
& wsl.exe -d $activeDistro -- bash -lc "omx doctor"
if ($LASTEXITCODE -ne 0) {
  Write-Warning "omx doctor reported an issue. Review the output above before using OMX for real work."
}

$projectWslPath = Convert-ToWslPath -Path (Get-Location).ProviderPath
Show-ManualConfigurationGuide -DistroName $activeDistro -ProjectWslPath $projectWslPath
