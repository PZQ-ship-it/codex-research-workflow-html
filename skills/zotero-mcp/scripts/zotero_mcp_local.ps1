param(
  [ValidateSet("status", "setup-source", "setup-env", "install", "mcp-config", "smoke")]
  [string]$Command = "status",
  [string]$RuntimeRoot,
  [string]$Python
)

$ErrorActionPreference = "Stop"

function Resolve-RuntimeRoot {
  if ($RuntimeRoot) {
    $resolved = Resolve-Path -LiteralPath $RuntimeRoot -ErrorAction SilentlyContinue
    if ($resolved) {
      return $resolved.Path
    }
    return $RuntimeRoot
  }
  if ($env:ZOTERO_MCP_RUNTIME) {
    return $env:ZOTERO_MCP_RUNTIME
  }
  return (Join-Path $env:LOCALAPPDATA "Codex\zotero-mcp")
}

function Test-Python310 {
  param([string]$Path)
  if (-not $Path -or -not (Test-Path -LiteralPath $Path)) {
    return $false
  }
  & $Path -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
  return ($LASTEXITCODE -eq 0)
}

function Find-Python310 {
  if ($Python -and (Test-Python310 $Python)) {
    return $Python
  }
  if ($env:ZOTERO_MCP_PYTHON -and (Test-Python310 $env:ZOTERO_MCP_PYTHON)) {
    return $env:ZOTERO_MCP_PYTHON
  }

  $candidates = @(
    "C:\ProgramData\Anaconda3\envs\devdefender-lab\python.exe",
    "C:\ProgramData\Anaconda3\envs\cogpace-bench\python.exe",
    "C:\ProgramData\Anaconda3\envs\gaokao_pg\python.exe",
    "C:\ProgramData\Anaconda3\envs\image-to-editable-ppt\python.exe",
    "C:\ProgramData\Anaconda3\envs\nano-claude\python.exe"
  )
  foreach ($candidate in $candidates) {
    if (Test-Python310 $candidate) {
      return $candidate
    }
  }

  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd -and (Test-Python310 $cmd.Source)) {
    return $cmd.Source
  }
  throw "No Python 3.10+ interpreter found. Set ZOTERO_MCP_PYTHON to a suitable python.exe."
}

function Get-Paths {
  $root = Resolve-RuntimeRoot
  $sourceRoot = Join-Path $root "source"
  $source = Join-Path $sourceRoot "54yyyu-zotero-mcp"
  $venv = Join-Path $root ".venv"
  return [PSCustomObject]@{
    Runtime = $root
    SourceRoot = $sourceRoot
    Source = $source
    Venv = $venv
    VenvPython = (Join-Path $venv "Scripts\python.exe")
    ZoteroMcp = (Join-Path $venv "Scripts\zotero-mcp.exe")
    ZoteroCli = (Join-Path $venv "Scripts\zotero-cli.exe")
  }
}

function Setup-Source {
  $p = Get-Paths
  New-Item -ItemType Directory -Force -Path $p.SourceRoot | Out-Null
  if (Test-Path -LiteralPath $p.Source) {
    git -C $p.Source fetch --depth 1 origin main
    git -C $p.Source checkout FETCH_HEAD
  } else {
    git clone --depth 1 https://github.com/54yyyu/zotero-mcp.git $p.Source
  }
  [PSCustomObject]@{
    Source = $p.Source
    Commit = (git -C $p.Source rev-parse HEAD)
    Status = ((git -C $p.Source status --short) -join "; ")
  }
}

function Setup-Env {
  $p = Get-Paths
  $py = Find-Python310
  New-Item -ItemType Directory -Force -Path $p.Runtime | Out-Null
  if (-not (Test-Path -LiteralPath $p.VenvPython)) {
    & $py -m venv $p.Venv
  }
  & $p.VenvPython -m pip install --upgrade pip setuptools wheel
  & $p.VenvPython -m pip install --upgrade zotero-mcp-server
  [PSCustomObject]@{
    Python = (& $p.VenvPython -c "import sys; print(sys.version.split()[0])")
    ZoteroMcp = $p.ZoteroMcp
    ZoteroCli = $p.ZoteroCli
    Version = (& $p.ZoteroMcp version)
  }
}

function Show-Status {
  $p = Get-Paths
  $localApi = "unavailable"
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:23119/api/" -UseBasicParsing -TimeoutSec 3
    $localApi = "HTTP $($r.StatusCode)"
  } catch {
    $localApi = "unavailable: $($_.Exception.Message)"
  }

  [PSCustomObject]@{
    Runtime = $p.Runtime
    SourceExists = (Test-Path -LiteralPath $p.Source)
    SourceCommit = $(if (Test-Path -LiteralPath $p.Source) { git -C $p.Source rev-parse HEAD } else { "" })
    VenvExists = (Test-Path -LiteralPath $p.VenvPython)
    ZoteroMcpExists = (Test-Path -LiteralPath $p.ZoteroMcp)
    ZoteroCliExists = (Test-Path -LiteralPath $p.ZoteroCli)
    ZoteroLocalApi = $localApi
  }
}

function Show-McpConfig {
  $p = Get-Paths
  @"
[mcp_servers.zotero]
command = '$($p.ZoteroMcp)'
args = ['serve']

[mcp_servers.zotero.env]
PYTHONIOENCODING = 'utf-8'
PYTHONUTF8 = '1'
ZOTERO_LOCAL = 'true'
"@
}

function Invoke-Smoke {
  $p = Get-Paths
  if (-not (Test-Path -LiteralPath $p.ZoteroMcp)) {
    throw "zotero-mcp.exe not found. Run install first."
  }
  & $p.ZoteroMcp version
  & $p.ZoteroMcp --help | Select-Object -First 20
  Show-Status
}

switch ($Command) {
  "setup-source" { Setup-Source }
  "setup-env" { Setup-Env }
  "install" {
    Setup-Source
    Setup-Env
  }
  "mcp-config" { Show-McpConfig }
  "smoke" { Invoke-Smoke }
  default { Show-Status }
}
