# Registers two Windows scheduled tasks for OrgChat (run once, in a normal PowerShell window):
#   OrgChat-Backup       daily at 02:00      -> python tools\backup_data.py
#   OrgChat-HealthCheck  every 5 minutes     -> python tools\healthcheck.py
# Usage:  powershell -ExecutionPolicy Bypass -File tools\install_scheduled_tasks.ps1
#         (add -Remove to delete the tasks again, -Python "C:\path\python.exe" to choose the interpreter)
param(
  [string]$Python = "",
  [string]$BackupDir = "C:\OrgChatBackups",
  [switch]$Remove
)
$ErrorActionPreference = "Stop"
$webai = Split-Path -Parent $PSScriptRoot
if ($Remove) {
  foreach ($n in "OrgChat-Backup", "OrgChat-HealthCheck") { schtasks /Delete /TN $n /F 2>$null | Out-Null }
  Write-Host "Removed scheduled tasks."; exit 0
}
if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$backupCmd = "`"$Python`" `"$webai\tools\backup_data.py`" --dest `"$BackupDir`" --keep 14"
$healthCmd = "`"$Python`" `"$webai\tools\healthcheck.py`""
schtasks /Create /F /TN "OrgChat-Backup"      /SC DAILY  /ST 02:00 /TR "cmd /c cd /d `"$webai`" && $backupCmd" | Out-Null
schtasks /Create /F /TN "OrgChat-HealthCheck" /SC MINUTE /MO 5     /TR "cmd /c cd /d `"$webai`" && $healthCmd" | Out-Null

Write-Host "Created tasks:"
schtasks /Query /TN "OrgChat-Backup" /FO LIST | Select-String "TaskName|Next Run Time"
schtasks /Query /TN "OrgChat-HealthCheck" /FO LIST | Select-String "TaskName|Next Run Time"
Write-Host "`nBackups go to $BackupDir (not inside OneDrive). Run a test now:  schtasks /Run /TN OrgChat-Backup"
Write-Host "Alerts: e-mail uses SMTP_* from .env (optionally ALERT_EMAIL); LINE push needs ALERT_LINE_USER_ID in .env."
