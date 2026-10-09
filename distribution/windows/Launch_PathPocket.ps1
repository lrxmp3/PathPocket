$ErrorActionPreference = "Stop"
$Distro = "Ubuntu-24.04"
$WslExe = Join-Path $env:SystemRoot "System32\wsl.exe"

if (-not (Test-Path -LiteralPath $WslExe)) {
    Write-Host "WSL is unavailable. Run Setup_First_Run.bat first."
    Read-Host "Press Enter to close"
    exit 2
}

try {
    $root = (& $WslExe -d $Distro --exec bash -lc 'cat "$HOME/.pathpocket_hf5_install_root" 2>/dev/null').Trim()
    if ([string]::IsNullOrWhiteSpace($root)) {
        Write-Host "PathPocket v1.0.6 is not installed. Run Setup_First_Run.bat first."
        Read-Host "Press Enter to close"
        exit 2
    }

    & $WslExe -d $Distro --exec bash "$root/PathPocket.sh"
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Write-Host "PathPocket failed to start with exit code $rc. Run Verify_Installation.bat and preserve its output plus the diagnostics folders."
        Read-Host "Press Enter to close"
    }
    exit $rc
}
catch {
    Write-Host "PathPocket launch failed: $($_.Exception.Message)"
    Read-Host "Press Enter to close"
    exit 1
}
