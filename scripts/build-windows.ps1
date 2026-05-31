param(
    [string]$EntryPoint = "scripts\gui_entry.py",
    [string]$Name = "DocumentConverter"
)

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

& $Python -m pip install --upgrade pyinstaller
& $Python -m PyInstaller --noconfirm --name $Name --paths src --collect-all docx --collect-all pypdf --add-data "schemas;schemas" --add-data "assets;assets" --windowed $EntryPoint

Write-Host "Build finished: dist\$Name"