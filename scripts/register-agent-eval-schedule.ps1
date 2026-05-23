param(
    [string]$TaskName = "DocumentConverterAgentEvalRefresh",
    [string]$DayOfWeek = "Monday",
    [string]$At = "09:00",
    [switch]$CheckOnly,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$RefreshScript = Join-Path $ProjectRoot "scripts\refresh_agent_eval.py"
$TaskArguments = "`"$RefreshScript`" --check --check-markdown"

$status = [ordered]@{
    schema_version = "agent-eval-schedule-plan.v1"
    task_name = $TaskName
    project_root = $ProjectRoot
    python = $PythonPath
    refresh_script = $RefreshScript
    arguments = $TaskArguments
    day_of_week = $DayOfWeek
    at = $At
    check_only = [bool]$CheckOnly
    force = [bool]$Force
}

if ($CheckOnly) {
    $status | ConvertTo-Json -Depth 3
    return
}

if (-not (Test-Path $PythonPath)) {
    throw "Project venv Python not found: $PythonPath"
}
if (-not (Test-Path $RefreshScript)) {
    throw "Refresh script not found: $RefreshScript"
}

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask -and -not $Force) {
    throw "Scheduled task already exists: $TaskName. Re-run with -Force to replace it."
}
if ($existingTask -and $Force) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $PythonPath -Argument $TaskArguments -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
Write-Host "Scheduled task registered: $TaskName"