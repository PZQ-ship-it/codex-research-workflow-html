param(
    [Parameter(Mandatory = $true)]
    [string]$PptxPath,

    [Parameter(Mandatory = $true)]
    [string]$OutDir,

    [switch]$ExportPdf
)

$ErrorActionPreference = "Stop"

$resolvedPptx = (Resolve-Path -LiteralPath $PptxPath).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$resolvedOutDir = (Resolve-Path -LiteralPath $OutDir).Path

$powerPoint = $null
$presentation = $null

try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue
    $presentation = $powerPoint.Presentations.Open($resolvedPptx, $true, $false, $false)

    $slideCount = $presentation.Slides.Count
    $pngDir = Join-Path $resolvedOutDir "rendered_pages"
    New-Item -ItemType Directory -Force -Path $pngDir | Out-Null

    for ($i = 1; $i -le $slideCount; $i++) {
        $outPath = Join-Path $pngDir ("slide_{0:D3}.png" -f $i)
        $presentation.Slides.Item($i).Export($outPath, "PNG", 1920, 1080)
    }

    $pdfPath = $null
    if ($ExportPdf) {
        $pdfPath = Join-Path $resolvedOutDir "deck_render.pdf"
        $presentation.SaveAs($pdfPath, 32)
    }

    [pscustomobject]@{
        status = "ok"
        pptx = $resolvedPptx
        out_dir = $resolvedOutDir
        slide_count = $slideCount
        png_dir = $pngDir
        pdf = $pdfPath
    } | ConvertTo-Json -Depth 4
}
finally {
    if ($presentation -ne $null) {
        $presentation.Close()
    }
    if ($powerPoint -ne $null) {
        $powerPoint.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) | Out-Null
    }
}
