$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Launch = Join-Path $PSScriptRoot "Launch_PathPocket.ps1"
$ShortcutPath = Join-Path $Desktop "PathPocket v1.0.6 (WSL2).lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Launch`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "PathPocket v1.0.6 via WSL2/WSLg"
$Shortcut.Save()
Write-Host "Created: $ShortcutPath"
