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
$RuntimeSha256 = "__RUNTIME_SHA256__"
$Diagnostics = Join-Path $PackageRoot "diagnostics"
New-Item -ItemType Directory -Force -Path $Diagnostics | Out-Null
$Log = Join-Path $Diagnostics ("windows_setup_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

function Log([string]$Level, [string]$Message) {
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    [Console]::WriteLine($line)
    [IO.File]::AppendAllText($Log, $line + [Environment]::NewLine, $Utf8NoBom)
}

function Get-Sha256Hex([string]$LiteralPath) {
    # Avoid module-provided hash cmdlets: fresh Windows images can differ in module loading.
    $algorithm = $null
    $stream = $null
    try {
        $algorithm = [System.Security.Cryptography.SHA256]::Create()
        $stream = [System.IO.File]::Open(
            $LiteralPath,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
        $bytes = $algorithm.ComputeHash($stream)
        return ([System.BitConverter]::ToString($bytes).Replace("-", "")).ToLowerInvariant()
    }
    catch {
        throw "SHA256 calculation failed for '$LiteralPath': $($_.Exception.Message)"
    }
    finally {
        if ($null -ne $stream) { $stream.Dispose() }
        if ($null -ne $algorithm) { $algorithm.Dispose() }
    }
}

function Invoke-WslSilent([string[]]$Arguments) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $script:WslExe @Arguments *> $null
        return $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previous
    }
}

function Invoke-WslCapture([string[]]$Arguments) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = @(& $script:WslExe @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
        $text = (($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine).Trim()
        return [pscustomobject]@{ ExitCode = $exitCode; Output = $text }
    }
    finally {
        $ErrorActionPreference = $previous
    }
}

function Invoke-WslLogged([string[]]$Arguments) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = @(& $script:WslExe @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
        foreach ($entry in $output) {
            $rendered = $entry.ToString().TrimEnd()
            if (-not [string]::IsNullOrWhiteSpace($rendered)) {
                foreach ($line in ($rendered -split "`r?`n")) {
                    Log "WSL" $line
                }
            }
        }
        return $exitCode
    }
    finally {
        $ErrorActionPreference = $previous
    }
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-WslState {
    $status = Invoke-WslCapture @("--status")
    $installed = Invoke-WslCapture @("--list", "--quiet")
    $names = @($installed.Output -split "`r?`n" | ForEach-Object { $_.Trim().Trim([char]0) } | Where-Object { $_ })
    if ($names -notcontains $Distro) {
        if ($status.ExitCode -ne 0) { return "A_NO_WSL" }
        return "B_NO_DISTRO"
    }

    $verbose = Invoke-WslCapture @("--list", "--verbose")
    $distroLine = @($verbose.Output -split "`r?`n" | Where-Object { $_ -match ("^\\s*\\*?\\s*" + [regex]::Escape($Distro) + ".*\\s2\\s*$") }) | Select-Object -First 1
    if (-not $distroLine) { return "C_DISTRO_NOT_WSL2" }

    $initialized = Invoke-WslCapture @("-d", $Distro, "-u", "root", "--exec", "/bin/sh", "-lc", "getent passwd 1000 >/dev/null 2>&1")
    if ($initialized.ExitCode -ne 0) { return "E_INITIALIZATION_REQUIRED" }
    return "D_READY"
}

function Invoke-ElevatedSelf {
    $arguments = @(
        "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"' + $PSCommandPath + '"'),
        "-ElevatedWslInstall",
        "-LinuxInstallParent", ('"' + $LinuxInstallParent + '"'),
        "-LinuxProjectRoot", ('"' + $LinuxProjectRoot + '"')
    )
    $child = Start-Process -FilePath $script:WindowsPowerShellExe -ArgumentList $arguments -Verb RunAs -Wait -PassThru
    exit $child.ExitCode
}

try {
    Log "INFO" "PathPocket v1.0.6 Windows/WSL2 installer repair build 20261009 started."
    Log "INFO" "Package directory: $PackageRoot"
    Log "INFO" "PowerShell version: $($PSVersionTable.PSVersion); edition: $($PSVersionTable.PSEdition); bitness: $([IntPtr]::Size * 8); PSHOME: $PSHOME"

    $script:WindowsPowerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    if (-not (Test-Path -LiteralPath $script:WindowsPowerShellExe)) {
        throw "The system Windows PowerShell executable is unavailable: $script:WindowsPowerShellExe"
    }
    Log "INFO" "PowerShell executable for elevation: $script:WindowsPowerShellExe"

    if ([string]::IsNullOrWhiteSpace($LinuxInstallParent)) { $LinuxInstallParent = '$HOME/Applications/PathPocket-v1.0.6' }
    if ([string]::IsNullOrWhiteSpace($LinuxProjectRoot)) { $LinuxProjectRoot = '$HOME/PathPocket Projects' }
    foreach ($linuxPath in @($LinuxInstallParent, $LinuxProjectRoot)) {
        if ($linuxPath -notmatch '^(\$HOME|/)' -or $linuxPath -match "[`r`n]") {
            throw "Linux install/project paths must start with `$HOME or / and must not contain a newline: $linuxPath"
        }
    }

    if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot "wsl_setup.sh"))) {
        throw "wsl_setup.sh is missing from the package directory: $PackageRoot"
    }
    $RuntimeArchive = Join-Path $PackageRoot $RuntimeRelativePath
    if (-not (Test-Path -LiteralPath $RuntimeArchive)) {
        $candidates = @(Get-ChildItem -LiteralPath $PackageRoot -Filter $RuntimeRelativePath -File -Recurse -ErrorAction SilentlyContinue)
        if ($candidates.Count -eq 1) {
            $RuntimeArchive = $candidates[0].FullName
            Log "RECOVERED_LAYOUT" "Found the nested Linux runtime archive in a child directory: $RuntimeArchive"
        }
        else {
            $visible = ((Get-ChildItem -LiteralPath $PackageRoot -Force | Select-Object -ExpandProperty Name) -join ", ")
            throw "The nested Linux runtime archive was not found. Expected: $(Join-Path $PackageRoot $RuntimeRelativePath). Package directory contains: $visible"
        }
    }

    Log "INFO" "Runtime SHA256 engine: .NET System.Security.Cryptography.SHA256."
    $actualRuntimeHash = Get-Sha256Hex $RuntimeArchive
    if ($actualRuntimeHash -ne $RuntimeSha256) {
        throw "The nested Linux runtime archive SHA256 is invalid. Expected $RuntimeSha256; got $actualRuntimeHash."
    }
    foreach ($required in @(
        "Setup_First_Run.bat", "Setup_First_Run.ps1", "Test_Package_Preflight.bat", "Test_Package_Preflight.ps1", "Verify_Installation.bat", "Create_Desktop_Shortcut.bat",
        "Launch_PathPocket.bat", "Launch_PathPocket.ps1", "INSTALL_WINDOWS_CN.md", "SHA256SUMS.txt",
        "WINDOWS_INSTALLER_REPAIR_20261009.md", "RELEASE_IDENTITY_20261009.json"
    )) {
        if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot $required))) {
            throw "Required package file is missing: $required"
        }
    }
    Log "PREFLIGHT_PASS" "Package structure, nested runtime and SHA256 are valid."
    if ($PreflightOnly) { exit 0 }

    $script:WslExe = Join-Path $env:SystemRoot "System32\wsl.exe"
    if (-not (Test-Path -LiteralPath $script:WslExe)) {
        throw "wsl.exe is unavailable. A supported 64-bit Windows 11 installation is required."
    }
    Log "INFO" "WSL executable: $script:WslExe"

    $state = Get-WslState
    Log "INFO" "Detected WSL state: $state"
    if ($state -eq "A_NO_WSL" -or $state -eq "B_NO_DISTRO") {
        if (-not $ElevatedWslInstall -and -not (Test-Administrator)) {
            Log "ACTION" "Administrator permission is required for the official WSL/Ubuntu installation."
            Invoke-ElevatedSelf
        }
        Log "ACTION" "Installing WSL2 and Ubuntu 24.04 with: wsl.exe --install -d Ubuntu-24.04"
        Log "INSTALL_IN_PROGRESS" "Official WSL installation is running. Its output and exit code are recorded below."
        $installCode = Invoke-WslLogged @("--install", "-d", $Distro)
        if ($installCode -ne 0) {
            throw "wsl.exe --install -d Ubuntu-24.04 failed with exit code $installCode."
        }
        Log "RESTART_REQUIRED" "WSL2/Ubuntu installation was requested successfully. Restart Windows if requested, open Ubuntu 24.04 once to create its username/password, then run this same Setup_First_Run.bat again. This is not an ordinary installation failure."
        exit 20
    }

    if ($state -eq "C_DISTRO_NOT_WSL2") {
        if (-not $ElevatedWslInstall -and -not (Test-Administrator)) {
            Log "ACTION" "Administrator permission is required for the official Ubuntu WSL2 conversion."
            Invoke-ElevatedSelf
        }
        Log "ACTION" "Ubuntu-24.04 exists but is not WSL2. Converting it with: wsl.exe --set-version Ubuntu-24.04 2"
        $convertCode = Invoke-WslLogged @("--set-version", $Distro, "2")
        if ($convertCode -ne 0) {
            throw "WSL2 conversion failed with exit code $convertCode."
        }
        $state = Get-WslState
        if ($state -ne "D_READY") {
            Log "RESTART_REQUIRED" "Ubuntu conversion completed but is not ready for PathPocket yet. Restart Windows if requested, complete Ubuntu initialization if prompted, then rerun this same Setup_First_Run.bat. This is not an ordinary installation failure."
            exit 20
        }
    }

    $state = Get-WslState
    if ($state -eq "E_INITIALIZATION_REQUIRED") {
        Log "INITIALIZATION_REQUIRED" "Ubuntu-24.04 is installed as WSL2, but its first Linux username/password has not been initialized. Open Ubuntu 24.04 once, complete that initialization, then rerun this same Setup_First_Run.bat. This is not an ordinary installation failure."
        exit 20
    }
    if ($state -ne "D_READY") {
        throw "Ubuntu-24.04 WSL2 readiness check failed."
    }
    Log "INFO" "Ubuntu-24.04 is running as WSL2."

    Log "ACTION" "Checking GPU with: wsl.exe -d Ubuntu-24.04 -- nvidia-smi"
    $gpuCode = Invoke-WslLogged @("-d", $Distro, "--", "nvidia-smi")
    if ($gpuCode -ne 0) {
        Log "GPU_FALLBACK" "The standard WSL GPU command was unavailable. Checking the official WSL GPU shim without modifying PATH or drivers."
        $gpuShimCode = Invoke-WslLogged @("-d", $Distro, "--", "/usr/lib/wsl/lib/nvidia-smi")
        if ($gpuShimCode -ne 0) {
            Log "GPU_UNAVAILABLE" "Both 'nvidia-smi' and '/usr/lib/wsl/lib/nvidia-smi' failed in WSL. This is a Windows/WSL GPU availability problem, not a missing PyTorch dependency. Do not install a Linux NVIDIA driver."
            exit 30
        }
        Log "GPU_AVAILABLE_VIA_WSL_SHIM" "WSL can access the NVIDIA GPU through /usr/lib/wsl/lib/nvidia-smi. No Linux NVIDIA driver, PATH modification, or Windows driver change was made."
    }
    else {
        Log "GPU_AVAILABLE" "WSL can access the NVIDIA GPU. PyTorch/CUDA Python packages may still be pending and will be checked by the Linux installer."
    }
    Log "INFO" "Starting the nested installer through official WSL --cd path handling; Unicode and spaces are passed directly by PowerShell."
    Log "INFO" "Linux installation parent: $LinuxInstallParent"
    Log "INFO" "Linux project root: $LinuxProjectRoot"
    Log "COMMAND" "wsl.exe --distribution $Distro --cd <package-directory> --exec env PATHPOCKET_INSTALL_PARENT=<selected> PATHPOCKET_PROJECT_ROOT=<selected> bash ./wsl_setup.sh"

    $setupCode = Invoke-WslLogged @(
        "--distribution", $Distro, "--cd", $PackageRoot, "--exec", "env",
        "PATHPOCKET_INSTALL_PARENT=$LinuxInstallParent", "PATHPOCKET_PROJECT_ROOT=$LinuxProjectRoot",
        "bash", "./wsl_setup.sh"
    )
    Log "EXIT_CODE" "wsl_setup.sh returned $setupCode"
    if ($setupCode -ne 0) {
        throw "The WSL PathPocket installer failed with exit code $setupCode. Review the COMMAND and captured WSL output in $Log."
    }
    Log "PASS" "PathPocket WSL2 installation completed. Run Create_Desktop_Shortcut.bat, then use the desktop shortcut."
    exit 0
}
catch {
    Log "ERROR" $_.Exception.Message
    Log "INFO" "Keep diagnostics and rerun the same installer after correcting the reported condition. Existing successful steps are preserved."
    exit 1
}
