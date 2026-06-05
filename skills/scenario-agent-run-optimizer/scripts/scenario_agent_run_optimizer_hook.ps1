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

if ([string]$event.hook_event_name -ne "UserPromptSubmit") {
    exit 0
}

$prompt = [string]$event.prompt
if ([string]::IsNullOrWhiteSpace($prompt)) {
    exit 0
}

$agentPattern = "(?i)(agent|multi[- ]?agent|assistant|bot|\u667A\u80FD\u4F53|\u4EE3\u7406|\u5BA2\u670D|\u52A9\u624B)"
$runPattern = "(?i)(trace|traces|log|logs|jsonl|otel|opentelemetry|langchain|langgraph|crewai|openai trace|anthropic trace|eval|evaluation|benchmark|run history|session|root[- ]?cause|failure|diagnos|optimi[sz]e|regression|golden|replay|\u8FD0\u884C\u65E5\u5FD7|\u65E5\u5FD7|\u8F68\u8FF9|\u8BC4\u4F30|\u8BC4\u6D4B|\u5931\u8D25|\u8BCA\u65AD|\u6839\u56E0|\u4F18\u5316|\u56DE\u653E|\u5BF9\u6BD4)"

if (($prompt -match $agentPattern) -and ($prompt -match $runPattern)) {
    Write-Json @{
        hookSpecificOutput = @{
            hookEventName = "UserPromptSubmit"
            additionalContext = 'This prompt appears to involve analyzing or optimizing an agent system from logs, traces, evals, failures, or run history. Consider using $scenario-agent-run-optimizer. Keep this advisory only: inventory evidence first, avoid secrets, and do not claim root causes without trace-backed evidence.'
        }
    }
}

