"""Owned-task control. Missing tasks are a successful no-op, never a hidden error."""
STOP_OWNED_TASKS = r"""
$ErrorActionPreference = 'Stop'
$wanted = @('AEDIGITAL Noon Monitor', 'AEDIGITAL Noon Public Monitor 10min')
try {
    $tasks = @(Get-ScheduledTask -ErrorAction Stop | Where-Object { $_.TaskName -in $wanted })
    foreach ($task in $tasks) {
        Stop-ScheduledTask -TaskName $task.TaskName -ErrorAction Stop
        Disable-ScheduledTask -TaskName $task.TaskName -ErrorAction Stop | Out-Null
    }
    Write-Output ('TASK_CHECK_OK: owned tasks found: ' + $tasks.Count)
    exit 0
} catch {
    [Console]::Error.WriteLine('TASK_CONTROL_FAILED: ' + $_.Exception.Message)
    exit 1
}
"""
