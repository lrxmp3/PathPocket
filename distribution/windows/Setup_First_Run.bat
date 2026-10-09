@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PACKAGE_ROOT=%~dp0"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%POWERSHELL_EXE%" (
  echo [ERROR] The system Windows PowerShell executable was not found.
  echo [ERROR] Expected: %POWERSHELL_EXE%
  if not defined PATHPOCKET_NO_PAUSE pause
  exit /b 1
)

pushd "%PACKAGE_ROOT%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Cannot enter the extracted package directory: %PACKAGE_ROOT%
  if not defined PATHPOCKET_NO_PAUSE pause
  exit /b 1
)

"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PACKAGE_ROOT%Setup_First_Run.ps1" %*
set "RC=%ERRORLEVEL%"
popd

echo.
if "%RC%"=="20" echo WSL installation was requested. Restart Windows if prompted, finish Ubuntu first launch, then run this file again.
if "%RC%"=="30" echo WSL2 is ready but the NVIDIA GPU is unavailable inside WSL. Do not install a Linux NVIDIA driver.
if not "%RC%"=="0" if not "%RC%"=="20" echo Installation did not complete. Keep this window and the diagnostics folder.
if not defined PATHPOCKET_NO_PAUSE pause
exit /b %RC%
