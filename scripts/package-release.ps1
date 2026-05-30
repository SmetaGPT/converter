param(
    [string]$Name = "DocumentConverter",
    [string]$Version = "0.3.0",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

if (-not $SkipBuild) {
    powershell -ExecutionPolicy Bypass -File "scripts\build-windows.ps1" -Name $Name
}

$distDir = Join-Path "dist" $Name
if (-not (Test-Path $distDir)) {
    throw "Build output not found: $distDir"
}

$releaseDir = Join-Path "dist\release" "$Name-$Version"
if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}
New-Item -ItemType Directory -Path $releaseDir | Out-Null

$stagingDir = Join-Path $releaseDir "package-staging"
New-Item -ItemType Directory -Path $stagingDir | Out-Null

$copied = $false
for ($attempt = 1; $attempt -le 10 -and -not $copied; $attempt++) {
    try {
        Copy-Item -Path (Join-Path $distDir "*") -Destination $stagingDir -Recurse -Force
        $copied = $true
    }
    catch {
        if ($attempt -ge 10) {
            throw
        }
        Start-Sleep -Milliseconds 500
    }
}

$zipPath = Join-Path $releaseDir "$Name-$Version-windows-portable.zip"
Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $stagingDir

$hash = Get-FileHash -Path $zipPath -Algorithm SHA256
$checksumPath = Join-Path $releaseDir "$Name-$Version-windows-portable.sha256.txt"
"$($hash.Hash.ToLower()) *$(Split-Path $zipPath -Leaf)" | Set-Content -Path $checksumPath -Encoding utf8

$releaseNotesPath = Join-Path $releaseDir "release-notes.md"
@"
# $Name $Version

- Artifact: $(Split-Path $zipPath -Leaf)
- SHA256: $($hash.Hash.ToLower())
- Packaging: portable Windows zip
- Semantic extraction: DOCX headers, footers, footnotes, formulas; PDF table/formula/figure units for text and OCR routes
- OCR core dependencies: ocrmypdf, tesseract, ghostscript
- Optional OCR helpers: jbig2, pngquant, verapdf
- Validation baseline:
    * python -m pip check
    * python -m ruff check src tests scripts
    * python -m pyright
    * python -m unittest discover -v
    * python scripts\run_synthetic_e2e.py --clean
    * powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name $Name
    * powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\$Name\$Name.exe
    * powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly
"@ | Set-Content -Path $releaseNotesPath -Encoding utf8

Write-Host "Release package created: $releaseDir"