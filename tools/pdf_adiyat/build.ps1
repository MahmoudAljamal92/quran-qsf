#requires -Version 5.1
<#
.SYNOPSIS
  Build the two Adiyat PDFs from the HTML sources using headless Microsoft Edge / Chrome.
  No Python, no pip, no external dependencies required — Edge ships with Windows 10/11.

.DESCRIPTION
  Reads:   tools/pdf_adiyat/poster.html   (A3 landscape, one page)
           tools/pdf_adiyat/analysis.html (A4 portrait,  six pages)
  Writes:  tools/pdf_adiyat/out/Adiyat_Infographic.pdf
           tools/pdf_adiyat/out/Adiyat_Analysis.pdf

  Page size (A3 landscape / A4 portrait) is driven by each HTML's CSS
  @page rule; Chromium respects it in headless print-to-PDF mode.

.NOTES
  Requires internet access the first run (Google Fonts download). The
  --virtual-time-budget=15000 flag gives fonts time to land before the
  PDF is snapshotted.
#>

[CmdletBinding()]
param(
    [switch]$OpenWhenDone
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$outDir = Join-Path $here 'out'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# ---- locate a Chromium-based browser ---------------------------------
function Find-Browser {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
        "${env:LOCALAPPDATA}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    throw "Could not locate Microsoft Edge or Google Chrome. Please install one, or pass -Browser <path>."
}

$browser = Find-Browser
Write-Host "Using browser: $browser" -ForegroundColor Cyan

# ---- convert a single html file to a pdf -----------------------------
function Convert-HtmlToPdf {
    param(
        [Parameter(Mandatory)] [string]$HtmlPath,
        [Parameter(Mandatory)] [string]$PdfPath
    )

    if (-not (Test-Path $HtmlPath)) { throw "Missing source HTML: $HtmlPath" }

    # file:// URL — Chromium requires forward slashes and three slashes
    $url = 'file:///' + ($HtmlPath -replace '\\', '/')

    # temp user-data-dir so we don't collide with a running Edge instance
    $userData = Join-Path $env:TEMP ("edge_pdf_" + [guid]::NewGuid().ToString('N'))

    $args = @(
        '--headless=new',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-dev-shm-usage',
        '--no-first-run',
        '--no-default-browser-check',
        '--hide-scrollbars',
        '--run-all-compositor-stages-before-draw',
        '--virtual-time-budget=15000',
        '--no-pdf-header-footer',
        "--user-data-dir=$userData",
        "--print-to-pdf=$PdfPath",
        $url
    )

    Write-Host "  -> building $(Split-Path $PdfPath -Leaf)" -ForegroundColor DarkGray

    $proc = Start-Process -FilePath $browser -ArgumentList $args -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "Browser exited with code $($proc.ExitCode). No PDF produced."
    }

    if (-not (Test-Path $PdfPath)) {
        throw "PDF was not created at $PdfPath."
    }

    # clean up the temp profile
    try { Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $userData } catch {}

    $size = [math]::Round((Get-Item $PdfPath).Length / 1KB, 1)
    Write-Host "     ok  ($size KB)" -ForegroundColor Green
}

# ---- build both ------------------------------------------------------
$jobs = @(
    @{ Html = 'poster.html';    Pdf = 'Adiyat_Infographic.pdf' },
    @{ Html = 'analysis.html';  Pdf = 'Adiyat_Analysis.pdf'    },
    @{ Html = 'deep_dive.html'; Pdf = 'Adiyat_DeepDive.pdf'    }
)

Write-Host ""
Write-Host "Building Adiyat PDFs..." -ForegroundColor Yellow
foreach ($j in $jobs) {
    $src = Join-Path $here $j.Html
    $dst = Join-Path $outDir $j.Pdf
    Convert-HtmlToPdf -HtmlPath $src -PdfPath $dst
}

Write-Host ""
Write-Host "Done. Output folder:" -ForegroundColor Yellow
Write-Host "  $outDir" -ForegroundColor White
Write-Host ""

if ($OpenWhenDone) {
    foreach ($j in $jobs) {
        Start-Process (Join-Path $outDir $j.Pdf)
    }
}
