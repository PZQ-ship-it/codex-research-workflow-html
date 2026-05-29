param(
    [string]$SkillDir = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"

$envPath = Join-Path $SkillDir ".env"
$secure = Read-Host "Enter OPENROUTER_ICU_API_KEY" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$plain = $null

try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ([string]::IsNullOrWhiteSpace($plain)) {
        throw "OPENROUTER_ICU_API_KEY is empty"
    }

    New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
    Set-Content -LiteralPath $envPath -Encoding UTF8 -Value ("OPENROUTER_ICU_API_KEY=" + $plain)
    "OPENROUTER_ICU_API_KEY saved to $envPath"
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $plain = $null
}
