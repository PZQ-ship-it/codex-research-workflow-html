#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_.-]+$')]
    [string]$ServerName,

    [int]$TimeoutSeconds = 600,
    [switch]$ShowAuthUrl,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[external-api-onboarding] $Message"
}

$status = [ordered]@{
    server_name = $ServerName
    timeout_seconds = $TimeoutSeconds
    dry_run = [bool]$DryRun
    show_auth_url = [bool]$ShowAuthUrl
    secret_values_printed = $false
    behavior = "Runs 'codex mcp login <server>', detects official auth URLs, and opens them in the default browser."
}

if ($DryRun) {
    $status | ConvertTo-Json -Depth 4
    exit 0
}

Write-Info "Starting Codex OAuth login for MCP server '$ServerName'."
Write-Info "When an official authorization URL appears, this helper opens it in the default browser."
Write-Info "Complete login, MFA, CAPTCHA, and consent in the browser. Do not paste tokens into chat."

$state = [hashtable]::Synchronized(@{
    opened = $false
    detected_url = $false
})

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = "codex"
$psi.Arguments = "mcp login $ServerName"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi

$handler = [System.Diagnostics.DataReceivedEventHandler]{
    param($sender, $eventArgs)
    if ([string]::IsNullOrWhiteSpace($eventArgs.Data)) {
        return
    }

    $line = $eventArgs.Data
    $matches = [regex]::Matches($line, 'https?://\S+')
    if ($matches.Count -gt 0) {
        foreach ($match in $matches) {
            $url = $match.Value.TrimEnd(")", ".", ",", ";")
            if ($url -match '/oauth/authorize|/authorize|/login|/mcp') {
                $state.detected_url = $true
                if (-not $state.opened) {
                    Start-Process $url
                    $state.opened = $true
                    Write-Host "[external-api-onboarding] Opened official authorization URL in the default browser."
                }
                if ($ShowAuthUrl) {
                    Write-Host "[external-api-onboarding] Authorization URL: $url"
                }
                return
            }
        }
    }

    if ($line -match 'token|secret|cookie|authorization:\s*bearer|api[_-]?key') {
        Write-Host "[external-api-onboarding] Suppressed potentially sensitive auth output."
    } else {
        Write-Host $line
    }
}

[void]$proc.Start()
$proc.add_OutputDataReceived($handler)
$proc.add_ErrorDataReceived($handler)
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while (-not $proc.HasExited) {
    if ((Get-Date) -gt $deadline) {
        try {
            $proc.Kill()
        } catch {
        }
        throw "Timed out waiting for OAuth login after $TimeoutSeconds seconds."
    }
    Start-Sleep -Seconds 1
}

if ($proc.ExitCode -ne 0) {
    throw "Codex OAuth login for '$ServerName' exited with code $($proc.ExitCode)."
}

Write-Info "OAuth login command finished for '$ServerName'."
Write-Info "Run 'codex mcp list' to confirm Auth status, and restart Codex if tools do not appear in the current session."
