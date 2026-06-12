#Requires -Version 5.1
[CmdletBinding()]
param(
    [string[]]$Provider = @("huggingface", "kaggle"),

    [int]$TimeoutSeconds = 600,
    [switch]$ShowAuthUrl,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[code-model-auth] $Message"
}

function Resolve-Providers {
    param([string[]]$Requested)

    $expanded = @()
    foreach ($item in $Requested) {
        foreach ($part in $item.Split(",")) {
            $value = $part.Trim().ToLowerInvariant()
            if ($value) {
                $expanded += $value
            }
        }
    }

    if ($expanded -contains "all") {
        return @("github", "huggingface", "kaggle")
    }

    $allowed = @("github", "huggingface", "kaggle")
    foreach ($value in $expanded) {
        if ($allowed -notcontains $value) {
            throw "Unsupported provider '$value'. Use github, huggingface, kaggle, or all."
        }
    }
    return @($expanded | Select-Object -Unique)
}

function Ensure-McpConfig {
    param([string]$Name)

    $setup = Join-Path $PSScriptRoot "setup_code_model_benchmark_intel.ps1"
    if (-not (Test-Path -LiteralPath $setup)) {
        throw "Setup script not found: $setup"
    }

    if ($Name -eq "huggingface") {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $setup -SkipPythonDeps -RegisterHuggingFaceMcp | Out-Host
    } elseif ($Name -eq "kaggle") {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $setup -SkipPythonDeps -RegisterKaggleMcp | Out-Host
    } elseif ($Name -eq "github") {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $setup -SkipPythonDeps -RegisterGitHubMcp | Out-Host
    }
}

function Open-OAuthLogin {
    param(
        [string]$ServerName,
        [int]$Timeout,
        [bool]$PrintUrl
    )

    Write-Info "Starting Codex OAuth login for $ServerName."
    Write-Info "A browser window will open when Codex emits the official authorization URL."
    Write-Info "Complete login/MFA/CAPTCHA/consent in the browser. No tokens will be printed by this helper."

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
        $urlMatches = [regex]::Matches($line, 'https?://\S+')
        if ($urlMatches.Count -gt 0) {
            foreach ($match in $urlMatches) {
                $url = $match.Value.TrimEnd(")", ".", ",", ";")
                if ($url -match '/oauth/authorize|/authorize|/login|/mcp') {
                    $state.detected_url = $true
                    if (-not $state.opened) {
                        Start-Process $url
                        $state.opened = $true
                        Write-Host "[code-model-auth] Opened official authorization URL for $ServerName in the default browser."
                    }
                    if ($PrintUrl) {
                        Write-Host "[code-model-auth] Authorization URL: $url"
                    }
                    return
                }
            }
        }

        if ($line -match 'token|secret|cookie|authorization:\s*bearer') {
            Write-Host "[code-model-auth] Suppressed potentially sensitive auth output from $ServerName."
        } else {
            Write-Host $line
        }
    }

    [void]$proc.Start()
    $proc.add_OutputDataReceived($handler)
    $proc.add_ErrorDataReceived($handler)
    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()

    $deadline = (Get-Date).AddSeconds($Timeout)
    while (-not $proc.HasExited) {
        if ((Get-Date) -gt $deadline) {
            try {
                $proc.Kill()
            } catch {
            }
            throw "Timed out waiting for $ServerName OAuth login after $Timeout seconds."
        }
        Start-Sleep -Seconds 1
    }

    if ($proc.ExitCode -ne 0) {
        throw "Codex OAuth login for $ServerName exited with code $($proc.ExitCode)."
    }

    Write-Info "OAuth login command finished for $ServerName."
}

$providers = Resolve-Providers -Requested $Provider
$status = [ordered]@{
    providers = $providers
    timeout_seconds = $TimeoutSeconds
    dry_run = [bool]$DryRun
    show_auth_url = [bool]$ShowAuthUrl
    secret_values_printed = $false
    notes = @(
        "huggingface and kaggle use Codex remote MCP OAuth.",
        "github uses bearer-token env var GITHUB_PAT_TOKEN, not an OAuth browser flow.",
        "This helper opens official auth URLs but does not read or store tokens."
    )
}

if ($DryRun) {
    $status | ConvertTo-Json -Depth 4
    exit 0
}

foreach ($providerName in $providers) {
    if ($providerName -eq "github") {
        Ensure-McpConfig -Name "github"
        Write-Info "GitHub MCP uses GITHUB_PAT_TOKEN, not browser OAuth."
        Write-Info "Opening GitHub fine-grained PAT creation page. Create a least-privilege token there, then store it outside chat."
        Start-Process "https://github.com/settings/personal-access-tokens/new"
        Write-Info "Use external-api-onboarding hidden secret storage or a user environment variable for GITHUB_PAT_TOKEN."
        continue
    }

    Ensure-McpConfig -Name $providerName
    Open-OAuthLogin -ServerName $providerName -Timeout $TimeoutSeconds -PrintUrl ([bool]$ShowAuthUrl)
}

Write-Info "Done. Run 'codex mcp list' to confirm Auth status, and restart Codex if tools do not appear in the current session."
