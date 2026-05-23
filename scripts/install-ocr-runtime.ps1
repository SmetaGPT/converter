param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$TessdataDir = Join-Path $HOME "scoop\persist\tesseract\tessdata"
$TrainedDataSha256 = @{
    eng = "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2"
    rus = "e16e5e036cce1d9ec2b00063cf8b54472625b9e14d893a169e2b0dedeb4df225"
    osd = "9cf5d576fcc47564f11265841e5ca839001e7e6f38ff7f7aacf46d15a96b00ff"
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandAvailable {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-CheckedCommand {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments
    )
    Write-Host "==> $Name"
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Assert-Sha256Match {
    param(
        [string]$Path,
        [string]$ExpectedSha256,
        [string]$ArtifactName
    )

    if (-not (Test-Path $Path)) {
        throw "$ArtifactName not found: $Path"
    }

    $actualSha256 = (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLower()
    $expectedSha256 = $ExpectedSha256.ToLower()
    if ($actualSha256 -ne $expectedSha256) {
        throw "SHA-256 mismatch for ${ArtifactName}: expected $expectedSha256, got $actualSha256"
    }
}

function Install-TessdataFile {
    param(
        [string]$Name
    )

    $expectedSha256 = $TrainedDataSha256[$Name]
    if (-not $expectedSha256) {
        throw "No expected SHA-256 configured for $Name traineddata"
    }

    New-Item -ItemType Directory -Force -Path $TessdataDir | Out-Null
    $target = Join-Path $TessdataDir "$Name.traineddata"
    $url = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/$Name.traineddata"
    Write-Host "==> Install Tesseract language $Name"
    & curl.exe -L $url -o $target
    if ($LASTEXITCODE -ne 0) {
        if (Test-Path $target) {
            Remove-Item -Force $target
        }
        throw "Failed to download $Name traineddata"
    }

    try {
        Assert-Sha256Match -Path $target -ExpectedSha256 $expectedSha256 -ArtifactName "$Name traineddata"
    }
    catch {
        if (Test-Path $target) {
            Remove-Item -Force $target
        }
        throw
    }
}

function Install-WithScoop {
    if (-not (Test-CommandAvailable "python")) {
        throw "python is required to create the project venv."
    }

    if (-not (Test-Path $VenvPython)) {
        Invoke-CheckedCommand -Name "Create project venv" -FilePath "python" -Arguments @("-m", "venv", (Join-Path $ProjectRoot ".venv"))
    }

    Invoke-CheckedCommand -Name "Upgrade venv tooling" -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    Invoke-CheckedCommand -Name "Install project package" -FilePath $VenvPython -Arguments @("-m", "pip", "install", "-e", $ProjectRoot)
    Invoke-CheckedCommand -Name "Install Tesseract and Ghostscript" -FilePath "scoop" -Arguments @("install", "tesseract", "ghostscript")
    Install-TessdataFile -Name "eng"
    Install-TessdataFile -Name "rus"
    Install-TessdataFile -Name "osd"
}

$status = [ordered]@{
    schema_version = "ocr-runtime-install-plan.v2"
    preferred_method = if (Test-CommandAvailable "scoop") { "scoop+venv" } else { "winget+choco" }
    requires_admin = -not (Test-CommandAvailable "scoop")
    is_admin = Test-Admin
    scoop = Test-CommandAvailable "scoop"
    winget = Test-CommandAvailable "winget"
    choco = Test-CommandAvailable "choco"
    python = Test-CommandAvailable "python"
    venv_python = Test-Path $VenvPython
    planned_steps = if (Test-CommandAvailable "scoop") {
        @(
            "python -m venv .venv (if missing)",
            ".\\.venv\\Scripts\\python.exe -m pip install -e .",
            "scoop install tesseract ghostscript",
            "download and verify eng/rus/osd traineddata into ~/scoop/persist/tesseract/tessdata"
        )
    } else {
        @(
            "winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements",
            "choco install ghostscript -y",
            "python -m pip install --upgrade ocrmypdf"
        )
    }
    traineddata_sha256 = [ordered]@{
        eng = $TrainedDataSha256.eng
        rus = $TrainedDataSha256.rus
        osd = $TrainedDataSha256.osd
    }
}

if ($CheckOnly) {
    $status | ConvertTo-Json -Depth 4
    return
}

if ($status.scoop) {
    Install-WithScoop
    Write-Host "OCR runtime install steps completed. Validate with:"
    Write-Host "  .\.venv\Scripts\python.exe -m doc_converter.cli check-ocr"
    return
}

if (-not $status.is_admin) {
    throw "Run this script from an elevated PowerShell session. Use -CheckOnly for a non-installing diagnostic."
}
if (-not $status.winget) {
    throw "winget is required to install UB-Mannheim Tesseract OCR."
}
if (-not $status.choco) {
    throw "Chocolatey is required to install Ghostscript with this helper. Install Ghostscript manually if Chocolatey is unavailable."
}
if (-not $status.python) {
    throw "python is required to install OCRmyPDF."
}

Invoke-CheckedCommand -Name "Install Tesseract OCR" -FilePath "winget" -Arguments @("install", "-e", "--id", "UB-Mannheim.TesseractOCR", "--accept-package-agreements", "--accept-source-agreements")
Invoke-CheckedCommand -Name "Install Ghostscript" -FilePath "choco" -Arguments @("install", "ghostscript", "-y")
Invoke-CheckedCommand -Name "Install OCRmyPDF" -FilePath "python" -Arguments @("-m", "pip", "install", "--upgrade", "ocrmypdf")

Write-Host "OCR runtime install steps completed. Restart PowerShell so PATH changes are visible, then run:"
Write-Host "  `$env:PYTHONPATH='src'; python -m doc_converter.cli check-ocr"
return