param(
  [string]$DistroName = "Ubuntu-24.04",
  [string]$LinuxUser = "codex",
  [string]$SourceCodexHome = "$env:USERPROFILE\.codex",
  [switch]$IncludePluginReference
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host "[codex-wsl-sync] $Message"
}

function Show-ManualConfigurationGuide {
  param(
    [string]$DistroName,
    [string]$LinuxUser,
    [switch]$PluginReferenceCopied
  )

  Write-Host ""
  Write-Host "Manual configuration guide"
  Write-Host "=========================="
  Write-Host "1. Open WSL and inspect the merged AGENTS guidance:"
  Write-Host "   wsl -d $DistroName"
  Write-Host "   sed -n '1,120p' ~/.codex/AGENTS.md"
  Write-Host ""
  Write-Host "2. Confirm the WSL-specific scope rules fit your workflow:"
  Write-Host "   - general language, safety, and working-style guidance should apply"
  Write-Host "   - Windows paths, PowerShell snippets, VS Code UI assumptions, and desktop automation are host-side references only"
  Write-Host "   - OMX-managed WSL config, hooks, skills, and AGENTS sections stay authoritative on conflicts"
  Write-Host ""
  Write-Host "3. Review Windows config as a reference before applying anything manually:"
  Write-Host "   less ~/.codex/config.windows-global.reference.toml"
  Write-Host "   vi ~/.codex/config.toml"
  Write-Host ""
  Write-Host "4. Recreate credentials and provider environment inside WSL manually:"
  Write-Host "   codex login"
  Write-Host "   codex login status"
  Write-Host "   # add proxy/provider/MCP env vars to ~/.bashrc only if needed"
  Write-Host ""
  Write-Host "5. Validate after any manual changes:"
  Write-Host "   omx doctor"
  Write-Host "   omx exec --skip-git-repo-check -C . `"Reply with exactly OMX-EXEC-OK`""
  Write-Host ""
  Write-Host "6. Recovery:"
  Write-Host "   backups are under ~/.codex/backups/windows-global-sync-<timestamp>"
  Write-Host "   restore files from the latest backup if a manual merge goes sideways"
  if ($PluginReferenceCopied) {
    Write-Host ""
    Write-Host "7. Plugin reference copy:"
    Write-Host "   Windows plugins were copied to ~/.codex/plugins-windows-reference for inspection only."
    Write-Host "   Do not treat them as active WSL plugins until you review paths and platform assumptions."
  }
}

function Copy-TreeToStage {
  param(
    [string]$Source,
    [string]$Destination
  )

  if (-not (Test-Path -LiteralPath $Source)) {
    return
  }

  New-Item -ItemType Directory -Force -Path $Destination | Out-Null

  $excludeDirs = @(
    ".git",
    ".qodo",
    ".sandbox",
    ".sandbox-bin",
    ".sandbox-secrets",
    ".tmp",
    "__pycache__",
    "computer-use",
    "log",
    "node_modules",
    "runtime",
    "sessions",
    "sqlite",
    "tmp",
    "vendor_imports"
  )

  $excludeFiles = @(
    ".codex-global-state.json",
    ".codex-global-state.json.bak",
    ".env",
    ".personality_migration",
    "*.log",
    "*.sqlite",
    "*.sqlite-shm",
    "*.sqlite-wal",
    "auth.json",
    "cap_sid",
    "history.jsonl",
    "installation_id",
    "session_index.jsonl",
    "version.json"
  )

  & robocopy $Source $Destination /E /NFL /NDL /NJH /NJS /NP /XD $excludeDirs /XF $excludeFiles | Out-Null
  $code = $LASTEXITCODE
  if ($code -ge 8) {
    throw "robocopy failed for $Source with exit code $code"
  }
  $global:LASTEXITCODE = 0
}

function Test-ConfigLooksSafeToReference {
  param([string]$Path)

  if (-not (Test-Path -LiteralPath $Path)) {
    return $false
  }

  $matches = Select-String -Path $Path -Pattern "(?i)(api[_-]?key|token|secret|password|credential|bearer)" -ErrorAction SilentlyContinue
  foreach ($match in $matches) {
    $line = $match.Line
    if ($line -match "^\s*#") {
      continue
    }
    if ($line -match "(?i)(env_var|_env|environment)") {
      continue
    }
    return $false
  }

  return $true
}

if (-not (Test-Path -LiteralPath $SourceCodexHome)) {
  throw "Source Codex home does not exist: $SourceCodexHome"
}

Write-Step "Checking WSL availability"
& wsl.exe -d $DistroName -- bash -lc "true"
if ($LASTEXITCODE -ne 0) {
  throw "WSL distro '$DistroName' is not reachable. If LxssManager is stuck, restart Windows and rerun this script."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stage = Join-Path $env:TEMP "codex-global-wsl-sync-$timestamp"
if (Test-Path -LiteralPath $stage) {
  Remove-Item -LiteralPath $stage -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $stage | Out-Null

Write-Step "Building non-sensitive import package at $stage"

$agentsPath = Join-Path $SourceCodexHome "AGENTS.md"
if (Test-Path -LiteralPath $agentsPath) {
  Copy-Item -LiteralPath $agentsPath -Destination (Join-Path $stage "AGENTS.windows.md") -Force
}

$configPath = Join-Path $SourceCodexHome "config.toml"
if (Test-ConfigLooksSafeToReference -Path $configPath) {
  Copy-Item -LiteralPath $configPath -Destination (Join-Path $stage "config.windows-global.reference.toml") -Force
} else {
  Write-Warning "Skipping config.toml reference copy because it contains secret-like literal lines."
}

foreach ($dir in @("skills", "rules", "memories")) {
  Copy-TreeToStage -Source (Join-Path $SourceCodexHome $dir) -Destination (Join-Path $stage $dir)
}

if ($IncludePluginReference) {
  Copy-TreeToStage -Source (Join-Path $SourceCodexHome "plugins") -Destination (Join-Path $stage "plugins-windows-reference")
}

$applyScript = @'
set -euo pipefail

linux_user="__LINUX_USER__"
target_home="$(getent passwd "$linux_user" | cut -d: -f6)"
if [ -z "$target_home" ] || [ ! -d "$target_home" ]; then
  echo "Cannot find home for user: $linux_user" >&2
  exit 1
fi

codex_home="$target_home/.codex"
import_root="/tmp/codex-global-import"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$codex_home/backups/windows-global-sync-$timestamp"

mkdir -p "$codex_home" "$backup_dir"

for item in AGENTS.md config.toml skills rules memories plugins-windows-reference config.windows-global.reference.toml; do
  if [ -e "$codex_home/$item" ]; then
    cp -a "$codex_home/$item" "$backup_dir/"
  fi
done

if [ -f "$import_root/config.windows-global.reference.toml" ]; then
  install -m 0600 -o "$linux_user" -g "$linux_user" \
    "$import_root/config.windows-global.reference.toml" \
    "$codex_home/config.windows-global.reference.toml"
fi

for dir in skills rules memories; do
  if [ -d "$import_root/$dir" ]; then
    mkdir -p "$codex_home/$dir"
    cp -a --update=none "$import_root/$dir/." "$codex_home/$dir/"
  fi
done

if [ -d "$import_root/plugins-windows-reference" ]; then
  mkdir -p "$codex_home/plugins-windows-reference"
  cp -a --update=none "$import_root/plugins-windows-reference/." "$codex_home/plugins-windows-reference/"
fi

if [ -f "$import_root/AGENTS.windows.md" ]; then
  if [ ! -f "$codex_home/AGENTS.md" ]; then
    touch "$codex_home/AGENTS.md"
  fi

  section_file="$(mktemp)"
  {
    echo "<!-- WINDOWS-GLOBAL-AGENTS-SYNC:START -->"
    echo "# Windows Global Guidance Adapted for WSL"
    echo
    echo "This section was imported from the Windows global Codex AGENTS.md, with WSL-specific scope rules added before the original guidance."
    echo
    echo "## WSL Scope Rules"
    echo
    echo "- Apply the language, safety, documentation, and working-style guidance as environment-neutral personal preferences."
    echo "- Prefer Linux shell paths and commands inside this WSL profile, for example \`~/.codex\`, \`/mnt/d/...\`, \`bash\`, \`apt\`, and \`tmux\`."
    echo "- Treat Windows-only paths, PowerShell snippets, VS Code UI assumptions, and desktop/browser automation as host-side guidance only, not automatic WSL commands."
    echo "- Do not copy, read, print, or preserve Windows secrets such as \`auth.json\`, \`.env\`, \`.sandbox-secrets\`, tokens, passwords, local session databases, or logs."
    echo "- Keep OMX-managed WSL config, hooks, skills, and AGENTS sections authoritative when they conflict with the imported Windows guidance."
    echo
    sed 's/\r$//' "$import_root/AGENTS.windows.md"
    echo
    echo "<!-- WINDOWS-GLOBAL-AGENTS-SYNC:END -->"
    echo
  } > "$section_file"

  python3 - "$codex_home/AGENTS.md" "$section_file" <<'PY'
from pathlib import Path
import sys

agents_path = Path(sys.argv[1])
section_path = Path(sys.argv[2])
start = "<!-- WINDOWS-GLOBAL-AGENTS-SYNC:START -->"
end = "<!-- WINDOWS-GLOBAL-AGENTS-SYNC:END -->"

text = agents_path.read_text(encoding="utf-8", errors="replace")
section = section_path.read_text(encoding="utf-8")

if start in text and end in text:
    before = text.split(start, 1)[0]
    after = text.split(end, 1)[1]
    merged = before + section + after.lstrip("\n")
else:
    merged = section + text

agents_path.write_text(merged, encoding="utf-8")
PY
fi

chown -R "$linux_user:$linux_user" "$codex_home"

echo "Synced Windows Codex guidance into $codex_home"
echo "Backup: $backup_dir"
'@

$applyScript = $applyScript.Replace("__LINUX_USER__", $LinuxUser)
$applyScriptPath = Join-Path $stage "apply-import.sh"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($applyScriptPath, $applyScript, $utf8NoBom)

Write-Step "Applying import inside WSL without using /mnt/c"
$cmd = 'tar -C "' + $stage + '" -cf - . | wsl.exe -d ' + $DistroName + ' -u root -- bash -lc "rm -rf /tmp/codex-global-import && mkdir -p /tmp/codex-global-import && tar -C /tmp/codex-global-import -xf - && bash /tmp/codex-global-import/apply-import.sh"'
& cmd.exe /d /c $cmd
if ($LASTEXITCODE -ne 0) {
  throw "WSL import failed with exit code $LASTEXITCODE"
}

Write-Step "Done. Active WSL config.toml was preserved; Windows config was copied as config.windows-global.reference.toml only."
Show-ManualConfigurationGuide -DistroName $DistroName -LinuxUser $LinuxUser -PluginReferenceCopied:$IncludePluginReference
