param(
    [switch]$ElevatedWslInstall,
    [switch]$PreflightOnly,
    [string]$LinuxInstallParent = "",
    [string]$LinuxProjectRoot = ""
)
$ErrorActionPreference = "Stop"
$Distro = "Ubuntu-24.04"
$PackageRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$RuntimeRelativePath = "linux-runtime.tar.gz"
$RuntimeSha256 = "21a9198534bb3942a986ba697ace93c38f136e55fa80c61a101e47ded90c2a4b"
$Diagnostics = Join-Path $PackageRoot "diagnostics"
New-Item -ItemType Directory -Force -Path $Diagnostics | Out-Null
$Log = Join-Path $Diagnostics ("windows_setup_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

if ([string]::IsNullOrWhiteSpace($LinuxInstallParent)) { $LinuxInstallParent = '$HOME/Applications/PathPocket-v1.0.6' }
if ([string]::IsNullOrWhiteSpace($LinuxProjectRoot)) { $LinuxProjectRoot = '$HOME/PathPocket Projects' }
foreach ($linuxPath in @($LinuxInstallParent, $LinuxProjectRoot)) {
    if ($linuxPath -notmatch '^(\$HOME|/)' -or $linuxPath -match "[`r`n]") {
        throw "Linux install/project paths must start with `$HOME or / and must not contain a newline: $linuxPath"
    }
}

function Log([string]$Level, [string]$Message) {
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    [Console]::WriteLine($line)
    [IO.File]::AppendAllText($Log, $line + [Environment]::NewLine, $Utf8NoBom)
}
function Invoke-WslSilent([string[]]$Arguments) {
    $previous = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { & $script:WslExe @Arguments *> $null; return $LASTEXITCODE }
    finally { $ErrorActionPreference = $previous }
}
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Get-WslState {
    $statusCode = Invoke-WslSilent @("--status")
    $distroCode = Invoke-WslSilent @("-d", $Distro, "--exec", "/bin/true")
    if ($distroCode -ne 0) {
        if ($statusCode -ne 0) { return "A_NO_WSL" }
        return "B_NO_DISTRO"
    }
    $previous = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { $kernel = ((& $script:WslExe -d $Distro --exec uname -r 2>$null) | Out-String).Trim() }
    finally { $ErrorActionPreference = $previous }
    if ($kernel -notmatch "(?i)WSL2") { return "C_DISTRO_NOT_WSL2" }
    return "D_READY"
}
function Invoke-ElevatedSelf {
    $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"' + $PSCommandPath + '"'), "-ElevatedWslInstall",
        "-LinuxInstallParent", ('"' + $LinuxInstallParent + '"'), "-LinuxProjectRoot", ('"' + $LinuxProjectRoot + '"'))
    $child = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru
    exit $child.ExitCode
}

try {
    Log "INFO" "PathPocket v1.0.6 NO_TARGETS HF5 Windows/WSL2 Installer HF3 started."
    Log "INFO" "Package directory: $PackageRoot"
    if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot "wsl_setup.sh"))) { throw "wsl_setup.sh is missing from the package directory: $PackageRoot" }
    $RuntimeArchive = Join-Path $PackageRoot $RuntimeRelativePath
    if (-not (Test-Path -LiteralPath $RuntimeArchive)) {
        $candidates = @(Get-ChildItem -LiteralPath $PackageRoot -Filter $RuntimeRelativePath -File -Recurse -ErrorAction SilentlyContinue)
        if ($candidates.Count -eq 1) {
            $RuntimeArchive = $candidates[0].FullName
            Log "RECOVERED_LAYOUT" "Found the nested Linux runtime archive in a child directory: $RuntimeArchive"
        } else {
            $visible = ((Get-ChildItem -LiteralPath $PackageRoot -Force | Select-Object -ExpandProperty Name) -join ", ")
            throw "The nested Linux runtime archive was not found. Expected: $(Join-Path $PackageRoot $RuntimeRelativePath). Package directory contains: $visible"
        }
    }
    $actualRuntimeHash = (Get-FileHash -LiteralPath $RuntimeArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualRuntimeHash -ne $RuntimeSha256) { throw "The nested Linux runtime archive SHA256 is invalid. Expected $RuntimeSha256; got $actualRuntimeHash." }
    foreach ($required in @("Setup_First_Run.bat", "Setup_First_Run.ps1", "Verify_Installation.bat", "Create_Desktop_Shortcut.bat", "INSTALL_WINDOWS_CN.md", "SHA256SUMS.txt")) {
        if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot $required))) { throw "Required package file is missing: $required" }
    }
    Log "PREFLIGHT_PASS" "Package structure, nested runtime and SHA256 are valid."
    if ($PreflightOnly) { exit 0 }
    $script:WslExe = Join-Path $env:SystemRoot "System32\wsl.exe"
    if (-not (Test-Path -LiteralPath $script:WslExe)) { throw "wsl.exe is unavailable. A supported 64-bit Windows 11 installation is required." }

    $state = Get-WslState
    Log "INFO" "Detected WSL state: $state"
    if ($state -eq "A_NO_WSL" -or $state -eq "B_NO_DISTRO") {
        if (-not $ElevatedWslInstall -and -not (Test-Administrator)) {
            Log "ACTION" "Administrator permission is required for the official WSL/Ubuntu installation."
            Invoke-ElevatedSelf
        }
        Log "ACTION" "Installing WSL2 and Ubuntu 24.04 with: wsl.exe --install -d Ubuntu-24.04"
        $installCode = Invoke-WslSilent @("--install", "-d", $Distro)
        if ($installCode -ne 0) { throw "wsl.exe --install -d Ubuntu-24.04 failed with exit code $installCode." }
        Log "RESTART_REQUIRED" "WSL2/Ubuntu installation was requested successfully. Restart Windows if requested, open Ubuntu 24.04 once to create its username/password, then run this same Setup_First_Run.bat again. This is not an ordinary installation failure."
        exit 20
    }
    if ($state -eq "C_DISTRO_NOT_WSL2") {
        Log "ACTION" "Ubuntu-24.04 exists but is not WSL2. Converting it with: wsl.exe --set-version Ubuntu-24.04 2"
        $convertCode = Invoke-WslSilent @("--set-version", $Distro, "2")
        if ($convertCode -ne 0) { throw "WSL2 conversion failed with exit code $convertCode." }
        if ((Get-WslState) -ne "D_READY") { throw "Ubuntu conversion returned success but WSL2 is not ready yet. Restart Windows and run setup again." }
    }
    if ((Get-WslState) -ne "D_READY") { throw "Ubuntu-24.04 WSL2 readiness check failed." }
    Log "INFO" "Ubuntu-24.04 is running as WSL2."

    $gpuCode = Invoke-WslSilent @("-d", $Distro, "--exec", "/usr/lib/wsl/lib/nvidia-smi")
    if ($gpuCode -ne 0) {
        Log "GPU_UNAVAILABLE" "WSL2 is ready, but 'wsl -d Ubuntu-24.04 -- nvidia-smi' failed. This is a Windows/WSL GPU availability problem, not a missing PyTorch dependency. Do not install a Linux NVIDIA driver."
        exit 30
    }
    Log "GPU_AVAILABLE" "WSL can access the NVIDIA GPU. PyTorch/CUDA Python packages may still be pending and will be checked by the Linux installer."
    Log "INFO" "Starting the nested installer through official WSL --cd path handling; Unicode and spaces are passed directly by PowerShell."
    Log "INFO" "Linux installation parent: $LinuxInstallParent"
    Log "INFO" "Linux project root: $LinuxProjectRoot"
    Log "COMMAND" "wsl.exe --distribution $Distro --cd <package-directory> --exec env PATHPOCKET_INSTALL_PARENT=<selected> PATHPOCKET_PROJECT_ROOT=<selected> bash ./wsl_setup.sh"
    $previous = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { & $script:WslExe --distribution $Distro --cd $PackageRoot --exec env "PATHPOCKET_INSTALL_PARENT=$LinuxInstallParent" "PATHPOCKET_PROJECT_ROOT=$LinuxProjectRoot" bash ./wsl_setup.sh 2>&1 | Tee-Object -FilePath $Log -Append; $setupCode = $LASTEXITCODE }
    finally { $ErrorActionPreference = $previous }
    Log "EXIT_CODE" "wsl_setup.sh returned $setupCode"
    if ($setupCode -ne 0) { throw "The WSL PathPocket installer failed with exit code $setupCode. Review the COMMAND and captured WSL output in $Log." }
    Log "PASS" "PathPocket WSL2 installation completed. Run Create_Desktop_Shortcut.bat, then use the desktop shortcut."
    exit 0
}
catch {
    Log "ERROR" $_.Exception.Message
    Log "INFO" "Keep diagnostics and rerun the same installer after correcting the reported condition. Existing successful steps are preserved."
    exit 1
}
