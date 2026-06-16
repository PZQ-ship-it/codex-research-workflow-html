param(
    [string]$SourceUrl = "https://github.com/HDdssX/dianping_crawler.git",
    [string]$TargetRoot = "",
    [switch]$WithVenv,
    [switch]$InstallBrowser,
    [switch]$RunSmoke
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $ScriptDir "cli.py"

$setupArgs = @("setup-source", "--source-url", $SourceUrl)
if ($TargetRoot -ne "") {
    $setupArgs += @("--target", $TargetRoot)
}
if ($WithVenv) {
    $setupArgs += "--with-venv"
}
if ($InstallBrowser) {
    $setupArgs += "--install-browser"
}

python $Cli @setupArgs

if ($RunSmoke) {
    $statusArgs = @("status")
    if ($TargetRoot -ne "") {
        $statusArgs += @("--crawler-root", $TargetRoot)
    }
    python $Cli @statusArgs
}
