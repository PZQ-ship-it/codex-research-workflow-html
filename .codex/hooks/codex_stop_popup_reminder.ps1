param()

$ErrorActionPreference = "SilentlyContinue"

function From-CodePoints($Codes) {
    $builder = New-Object System.Text.StringBuilder
    foreach ($code in $Codes) {
        [void]$builder.Append([char][int]$code)
    }
    $builder.ToString()
}

function Quote-PowerShellString($Value) {
    [char]39 + ([string]$Value).Replace([char]39, ([string][char]39 + [char]39)) + [char]39
}

function Read-StdinUtf8() {
    $inputStream = [Console]::OpenStandardInput()
    $memoryStream = New-Object System.IO.MemoryStream
    $buffer = New-Object byte[] 4096
    while (($read = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        $memoryStream.Write($buffer, 0, $read)
    }
    [System.Text.Encoding]::UTF8.GetString($memoryStream.ToArray())
}

function Has-Cjk($Value) {
    foreach ($ch in ([string]$Value).ToCharArray()) {
        $code = [int][char]$ch
        if (($code -ge 0x3400 -and $code -le 0x9fff) -or ($code -ge 0xf900 -and $code -le 0xfaff)) {
            return $true
        }
    }
    return $false
}

function Get-TextContent($Content) {
    if ($null -eq $Content) {
        return ""
    }
    if ($Content -is [string]) {
        return [string]$Content
    }
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($Content)) {
        if ($null -eq $item) {
            continue
        }
        if ($item.PSObject.Properties.Name -contains "text") {
            [void]$parts.Add([string]$item.text)
        }
    }
    ($parts -join " ").Trim()
}

function Is-ScaffoldPrompt($Text) {
    $value = [string]$Text
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $true
    }
    if ($value -match "(?is)#\s*AGENTS\.md|<INSTRUCTIONS>|</INSTRUCTIONS>|<environment_context>|</environment_context>|### Available skills") {
        return $true
    }
    return $false
}

function Get-TranscriptTexts($Path) {
    $result = @{
        User = New-Object System.Collections.Generic.List[string]
        Assistant = New-Object System.Collections.Generic.List[string]
    }
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return $result
    }
    try {
        foreach ($line in [System.IO.File]::ReadLines($Path, [System.Text.Encoding]::UTF8)) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }
            try {
                $record = $line | ConvertFrom-Json
            }
            catch {
                continue
            }
            if ([string]$record.type -ne "response_item") {
                continue
            }
            $payload = $record.payload
            if ($null -eq $payload -or [string]$payload.type -ne "message") {
                continue
            }
            $text = Get-TextContent $payload.content
            if ([string]::IsNullOrWhiteSpace($text)) {
                continue
            }
            if ([string]$payload.role -eq "user") {
                if (-not (Is-ScaffoldPrompt $text)) {
                    [void]$result.User.Add($text)
                }
            }
            elseif ([string]$payload.role -eq "assistant") {
                [void]$result.Assistant.Add($text)
            }
        }
    }
    catch {
    }
    $result
}

function Limit-Title($Value, $MaxChars) {
    $text = ([string]$Value).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) {
        return "Codex task"
    }
    if ($text.Length -le $MaxChars) {
        return $text
    }
    return $text.Substring(0, $MaxChars).Trim()
}

function Normalize-PlainText($Text) {
    $value = [string]$Text
    $value = [regex]::Replace($value, '```[\s\S]*?```', ' ')
    $value = [regex]::Replace($value, '\[[^\]]+\]\([^)]+\)', ' ')
    $value = [regex]::Replace($value, '[\$`*_>#\[\]{}()<>"\.,;:!?/\\|+=~]', ' ')
    $value = $value.Replace([string][char]39, " ")
    $value = [regex]::Replace($value, '[\r\n\t]+', ' ')
    $value = [regex]::Replace($value, '\s+', ' ').Trim()
    $value
}

function Remove-CjkNoise($Text) {
    $noise = @(
        @(0x8BF7), @(0x5E2E,0x6211), @(0x9700,0x8981), @(0x6211,0x9700,0x8981), @(0x6211,0x8981),
        @(0x8FD9,0x4E2A), @(0x90A3,0x4E2A), @(0x4E00,0x4E2A), @(0x4E00,0x4E0B),
        @(0x8FDB,0x884C), @(0x5E94,0x8BE5), @(0x6B63,0x5E38), @(0x5F53,0x524D),
        @(0x5927,0x6982), @(0x4EE5,0x5185), @(0x6216,0x8005), @(0x56E0,0x4E3A),
        @(0x53EF,0x80FD), @(0x540C,0x65F6), @(0x7A97,0x53E3), @(0x9875,0x9762),
        @(0x65F6,0x5019), @(0x6700,0x7B80), @(0x5408,0x9002), @(0x5B9E,0x73B0),
        @(0x65B9,0x5F0F), @(0x5E76,0x5C06,0x5176), @(0x5C06,0x5176),
        @(0x5168,0x5C40), @(0x7684)
    )
    $value = [string]$Text
    foreach ($codes in $noise) {
        $value = $value.Replace((From-CodePoints $codes), "")
    }
    $value
}

function Contains-CodeText($Text, $Codes) {
    ([string]$Text).Contains((From-CodePoints $Codes))
}

function Known-TitlePattern($Text) {
    $value = [string]$Text
    $hasGlobalHook = (Contains-CodeText $value @(0x5168,0x5C40,0x94A9,0x5B50)) -or (Contains-CodeText $value @(0x5168,0x5C40,0x20,0x68,0x6F,0x6F,0x6B))
    $hasAsyncWork = (Contains-CodeText $value @(0x5F02,0x6B65,0x4F5C,0x4E1A)) -or (Contains-CodeText $value @(0x5F02,0x6B65,0x4EFB,0x52A1))
    $hasRemove = (Contains-CodeText $value @(0x5220,0x6389)) -or (Contains-CodeText $value @(0x5220,0x9664)) -or (Contains-CodeText $value @(0x79FB,0x9664))
    if ($hasGlobalHook -and $hasAsyncWork -and $hasRemove) {
        return (From-CodePoints @(0x5F02,0x6B65,0x94A9,0x5B50,0x5220,0x9664))
    }
    $hasDesktopReminder = Contains-CodeText $value @(0x684C,0x9762,0x63D0,0x9192)
    $hasPopupReminder = (Contains-CodeText $value @(0x5F39,0x7A97,0x63D0,0x9192)) -or (Contains-CodeText $value @(0x5F39,0x51FA,0x5F0F,0x63D0,0x9192))
    $hasTitleNeed = (Contains-CodeText $value @(0x6807,0x9898)) -or (Contains-CodeText $value @(0x533A,0x5206)) -or ($value -match "(?i)\bxxx\b")
    if (($hasDesktopReminder -or $hasPopupReminder) -and $hasTitleNeed) {
        return (From-CodePoints @(0x684C,0x9762,0x63D0,0x9192,0x6807,0x9898))
    }
    if ($hasPopupReminder -and $value -match "(?i)codex") {
        return "Codex" + (From-CodePoints @(0x5F39,0x7A97,0x63D0,0x9192))
    }
    if ($value -match "(?i)stop\s*hook" -and (Contains-CodeText $value @(0x9A8C,0x8BC1))) {
        return "Stop hook" + (From-CodePoints @(0x9A8C,0x8BC1))
    }
    return ""
}

function Compact-MixedTitle($Text) {
    $builder = New-Object System.Text.StringBuilder
    $token = New-Object System.Text.StringBuilder
    $stop = @("windows","please","help","make","add","update","fix","implement","create","run","test","check","task","done","finished","complete","completed","use","using")
    function Flush-Token {
        if ($token.Length -eq 0) {
            return
        }
        $word = $token.ToString()
        [void]$token.Clear()
        if ($stop -contains $word.ToLowerInvariant()) {
            return
        }
        if ($word.Length -gt 12) {
            $word = $word.Substring(0, 12)
        }
        [void]$builder.Append($word)
    }
    foreach ($ch in ([string]$Text).ToCharArray()) {
        $code = [int][char]$ch
        if (($code -ge 0x3400 -and $code -le 0x9fff) -or ($code -ge 0xf900 -and $code -le 0xfaff)) {
            Flush-Token
            [void]$builder.Append($ch)
        }
        elseif (($code -ge 0x30 -and $code -le 0x39) -or ($code -ge 0x41 -and $code -le 0x5a) -or ($code -ge 0x61 -and $code -le 0x7a) -or $code -eq 0x2d -or $code -eq 0x5f) {
            [void]$token.Append($ch)
        }
        else {
            Flush-Token
        }
    }
    Flush-Token
    $builder.ToString()
}

function Build-TitleFromText($Text, $FallbackCwd) {
    $clean = Normalize-PlainText $Text
    if ([string]::IsNullOrWhiteSpace($clean)) {
        return (Title-From-Cwd $FallbackCwd)
    }
    if ($clean -match "[$]([A-Za-z0-9_-]{3,40})") {
        return (Limit-Title $matches[1] 20)
    }
    $known = Known-TitlePattern $clean
    if (-not [string]::IsNullOrWhiteSpace($known)) {
        return (Limit-Title $known 20)
    }
    if (Has-Cjk $clean) {
        $candidate = Remove-CjkNoise $clean
        $candidate = Compact-MixedTitle $candidate
        return (Limit-Title $candidate 20)
    }
    $words = [regex]::Matches($clean.ToLowerInvariant(), "[a-z0-9][a-z0-9_-]*") | ForEach-Object { $_.Value }
    $stop = @("the","a","an","to","for","of","in","on","and","or","with","from","this","that","please","help","make","add","update","fix","implement","create","run","test","check","codex","task","done","finished","complete","completed","use","using")
    $picked = New-Object System.Collections.Generic.List[string]
    foreach ($word in $words) {
        if ($stop -contains $word) {
            continue
        }
        [void]$picked.Add($word)
        if ($picked.Count -ge 4) {
            break
        }
    }
    if ($picked.Count -gt 0) {
        return (Limit-Title (($picked -join " ")) 20)
    }
    return (Limit-Title $clean 20)
}

function Title-From-Cwd($Cwd) {
    if (-not [string]::IsNullOrWhiteSpace($Cwd)) {
        $leaf = Split-Path -Leaf $Cwd
        if (-not [string]::IsNullOrWhiteSpace($leaf)) {
            return (Limit-Title $leaf 20)
        }
    }
    "Codex task"
}

function Get-Sha256Prefix($Value) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes([string]$Value)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash($bytes)
        (($hash[0..7] | ForEach-Object { $_.ToString("x2") }) -join "")
    }
    finally {
        $sha.Dispose()
    }
}

function Choose-TaskTitle($Event) {
    foreach ($name in @("task", "title", "summary", "prompt", "user_prompt")) {
        if ($null -ne $Event -and $Event.PSObject.Properties.Name -contains $name) {
            $value = [string]$Event.$name
            if (-not [string]::IsNullOrWhiteSpace($value) -and -not (Is-ScaffoldPrompt $value)) {
                return (Build-TitleFromText $value ([string]$Event.cwd))
            }
        }
    }
    $transcriptPath = ""
    foreach ($name in @("transcript_path", "transcriptPath")) {
        if ($null -ne $Event -and $Event.PSObject.Properties.Name -contains $name) {
            $transcriptPath = [string]$Event.$name
            break
        }
    }
    $texts = Get-TranscriptTexts $transcriptPath
    if ($texts.User.Count -gt 0) {
        return (Build-TitleFromText $texts.User[$texts.User.Count - 1] ([string]$Event.cwd))
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$Event.last_assistant_message)) {
        return (Build-TitleFromText ([string]$Event.last_assistant_message) ([string]$Event.cwd))
    }
    if ($texts.Assistant.Count -gt 0) {
        return (Build-TitleFromText $texts.Assistant[$texts.Assistant.Count - 1] ([string]$Event.cwd))
    }
    return (Title-From-Cwd ([string]$Event.cwd))
}

function Write-StopMarker($Event, $Title) {
    $markerPath = [string]$env:CODEX_STOP_MARKER_PATH
    if ([string]::IsNullOrWhiteSpace($markerPath)) {
        return
    }
    try {
        $parent = Split-Path -Parent $markerPath
        if (-not [string]::IsNullOrWhiteSpace($parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }

        $cwd = ""
        if ($null -ne $Event -and $Event.PSObject.Properties.Name -contains "cwd") {
            $cwd = [string]$Event.cwd
        }
        $cwdLabel = ""
        if (-not [string]::IsNullOrWhiteSpace($cwd)) {
            $cwdLabel = Split-Path -Leaf $cwd
        }

        $marker = [ordered]@{
            timestamp_utc = [DateTime]::UtcNow.ToString("o")
            source = "codex_stop_popup_reminder"
            hook_event_name = "Stop"
            cwd_label = $cwdLabel
            cwd_hash = Get-Sha256Prefix $cwd
            title_length = ([string]$Title).Length
            script_version = "2026-07-07-marker-v1"
        }
        $line = $marker | ConvertTo-Json -Compress
        [System.IO.File]::AppendAllText($markerPath, $line + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
    }
    catch {
    }
}

$raw = Read-StdinUtf8
$event = $null
if (-not [string]::IsNullOrWhiteSpace($raw)) {
    try {
        $event = $raw | ConvertFrom-Json
    }
    catch {
        $event = $null
    }
}

$eventName = ""
if ($null -ne $event -and $event.PSObject.Properties.Name -contains "hook_event_name") {
    $eventName = [string]$event.hook_event_name
}
if ($eventName -and $eventName -ne "Stop") {
    exit 0
}

$taskTitle = Choose-TaskTitle $event
$done = From-CodePoints @(0x5DF2, 0x5B8C, 0x6210)
$title = $taskTitle + $done
$message = $title

Write-StopMarker $event $title

if ([string]$env:CODEX_STOP_REMINDER_TEST -eq "1") {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
    [Console]::WriteLine($title)
    exit 0
}

$quotedTitle = Quote-PowerShellString $title
$quotedMessage = Quote-PowerShellString $message
$toastScript = @(
    '$ErrorActionPreference = "SilentlyContinue"',
    'Add-Type -AssemblyName System.Windows.Forms | Out-Null',
    'Add-Type -AssemblyName System.Drawing | Out-Null',
    '$notify = New-Object System.Windows.Forms.NotifyIcon',
    '$notify.Icon = [System.Drawing.SystemIcons]::Information',
    '$notify.BalloonTipTitle = ' + $quotedTitle,
    '$notify.BalloonTipText = ' + $quotedMessage,
    '$notify.Visible = $true',
    '$notify.ShowBalloonTip(8000)',
    '[System.Media.SystemSounds]::Asterisk.Play()',
    'Start-Sleep -Seconds 9',
    '$notify.Dispose()'
) -join [Environment]::NewLine

try {
    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($toastScript))
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-EncodedCommand",
        $encoded
    ) -WindowStyle Hidden | Out-Null
}
catch {
    try {
        Add-Type -AssemblyName PresentationFramework | Out-Null
        [System.Windows.MessageBox]::Show($message, $title) | Out-Null
    }
    catch {
        [Console]::Beep(880, 250)
    }
}

exit 0
