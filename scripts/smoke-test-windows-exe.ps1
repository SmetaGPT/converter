param(
    [Parameter(Mandatory = $true)]
    [string]$ExePath,
    [int]$AliveMilliseconds = 3000
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "EXE not found: $ExePath"
}

$process = Start-Process -FilePath $ExePath -PassThru

try {
    if ($process.WaitForExit($AliveMilliseconds)) {
        throw "EXE exited too early with code $($process.ExitCode): $ExePath"
    }
}
finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $null = $process.WaitForExit(5000)
    }
}

Write-Host "EXE smoke passed: $ExePath"