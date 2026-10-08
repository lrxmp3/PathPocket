$ErrorActionPreference = "Stop"
$Distro = "Ubuntu-24.04"
$root = (& wsl.exe -d $Distro -- bash -c 'cat $HOME/.pathpocket_hf5_install_root').Trim()
if ([string]::IsNullOrEmpty($root)) {
    Write-Host "PathPocket v1.0.6 is not installed. Run Setup_First_Run.bat first."
    Read-Host "Press Enter to close"
    exit 2
}
& wsl.exe -d $Distro -- bash "$root/PathPocket.sh"
$rc = $LASTEXITCODE
if ($rc -ne 0) {
    Write-Host "PathPocket failed to start with exit code $rc. Run Verify_Installation.bat and preserve its output plus the diagnostics folders."
    Read-Host "Press Enter to close"
}
exit $rc
