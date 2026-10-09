$ErrorActionPreference = "Stop"

# Regression sentinel: a package that reintroduces the old module hash command must fail here.
function Get-FileHash {
    throw "Regression: the installer attempted to use the module-provided hash command."
}

$installer = Join-Path $PSScriptRoot "Setup_First_Run.ps1"
if (-not (Test-Path -LiteralPath $installer)) {
    Write-Host "Package preflight: FAIL. Missing installer script: $installer"
    exit 1
}

& $installer -PreflightOnly
exit $LASTEXITCODE
