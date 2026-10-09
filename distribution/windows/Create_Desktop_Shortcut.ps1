$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Launch = Join-Path $PSScriptRoot "Launch_PathPocket.ps1"
$PowerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$ShortcutPath = Join-Path $Desktop "PathPocket v1.0.6 (WSL2).lnk"

if (-not (Test-Path -LiteralPath $Launch)) {
    throw "Launch script is missing: $Launch"
}
if (-not (Test-Path -LiteralPath $PowerShellExe)) {
    throw "The system Windows PowerShell executable is unavailable: $PowerShellExe"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PowerShellExe
$Shortcut.Arguments = "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$Launch`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "PathPocket v1.0.6 via WSL2/WSLg"
$Shortcut.Save()
Write-Host "Created: $ShortcutPath"
