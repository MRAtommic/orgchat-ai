# Registers two Windows scheduled tasks for OrgChat (run once, in a normal PowerShell window):
#   OrgChat-Backup       daily at 02:00      -> python tools\backup_data.py
#   OrgChat-HealthCheck  every 5 minutes     -> python tools\healthcheck.py
# Usage:  powershell -ExecutionPolicy Bypass -File tools\install_scheduled_tasks.ps1
#         (add -Remove to delete the tasks again, -Python "C:\path\python.exe" to choose the interpreter)
# Uses the ScheduledTasks cmdlets (the old schtasks /TR option is limited to 261 characters).
param(
  [string]$Python = "",
  [string]$BackupDir = "C:\OrgChatBackups",
  [switch]$Remove
)
$ErrorActionPreference = "Stop"
$webai = Split-Path -Parent $PSScriptRoot
if ($Remove) {
  foreach ($n in "OrgChat-Backup", "OrgChat-HealthCheck") { Unregister-ScheduledTask -TaskName $n -Confirm:$false -ErrorAction SilentlyContinue }
  Write-Host "Removed scheduled tasks."; exit 0
}
if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew

$backupAction = New-ScheduledTaskAction -Execute $Python -Argument "tools\backup_data.py --dest `"$BackupDir`" --keep 14" -WorkingDirectory $webai
$backupTrig   = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -TaskName "OrgChat-Backup" -Action $backupAction -Trigger $backupTrig -Settings $settings -Force | Out-Null

$healthAction = New-ScheduledTaskAction -Execute $Python -Argument "tools\healthcheck.py" -WorkingDirectory $webai
$healthTrig   = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "OrgChat-HealthCheck" -Action $healthAction -Trigger $healthTrig -Settings $settings -Force | Out-Null

Write-Host "Created tasks:"
foreach ($n in "OrgChat-Backup", "OrgChat-HealthCheck") {
  $i = Get-ScheduledTaskInfo -TaskName $n
  Write-Host ("  {0,-20} next run: {1}" -f $n, $i.NextRunTime)
}
Write-Host "`nBackups go to $BackupDir (not inside OneDrive). Run a test now:  Start-ScheduledTask -TaskName OrgChat-Backup"
Write-Host "Alerts: e-mail uses SMTP_* from .env (optionally ALERT_EMAIL); LINE push needs ALERT_LINE_USER_ID in .env."
