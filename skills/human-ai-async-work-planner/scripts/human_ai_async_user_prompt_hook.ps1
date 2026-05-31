param()

$ErrorActionPreference = "Stop"

function Write-Json($Object) {
    $Object | ConvertTo-Json -Depth 8 -Compress
}

$inputStream = [Console]::OpenStandardInput()
$memoryStream = New-Object System.IO.MemoryStream
$buffer = New-Object byte[] 4096
while (($read = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
    $memoryStream.Write($buffer, 0, $read)
}
$raw = [System.Text.Encoding]::UTF8.GetString($memoryStream.ToArray())
if ([string]::IsNullOrWhiteSpace($raw)) {
    exit 0
}

try {
    $event = $raw | ConvertFrom-Json
}
catch {
    exit 0
}

$eventName = [string]$event.hook_event_name
if ($eventName -ne "UserPromptSubmit") {
    exit 0
}

$prompt = [string]$event.prompt
if ([string]::IsNullOrWhiteSpace($prompt)) {
    exit 0
}

$longRunPattern = "(?i)(benchmark|render|generate|build|test|run|search|crawl|scrape|compile|train|evaluate|batch|long[- ]?running|background|while you work|while AI|PPT|deck|slide|screenshot|PDF|LaTeX|browser|Playwright|\u8DD1|\u8FD0\u884C|\u6D4B\u8BD5|\u6E32\u67D3|\u751F\u6210|\u68C0\u7D22|\u641C\u7D22|\u6279\u91CF|\u7B49\u5F85|\u540E\u53F0|\u957F\u4EFB\u52A1|\u8DD1\u6279)"

if ($prompt -match $longRunPattern) {
    Write-Json @{
        hookSpecificOutput = @{
            hookEventName = "UserPromptSubmit"
            additionalContext = 'If this prompt starts noticeable waiting time or background AI work, consider using $human-ai-async-work-planner before execution. Ask whether the user has another task queue, define a human lane, protect do-not-touch files, and set a return checkpoint. Keep this advisory; skip it for short or simple tasks.'
        }
    }
}
