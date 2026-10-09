@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PACKAGE_ROOT=%~dp0"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL_EXE%" (
  echo [ERROR] The system Windows PowerShell executable was not found: %POWERSHELL_EXE%
  pause
  exit /b 1
)
pushd "%PACKAGE_ROOT%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Cannot enter package directory: %PACKAGE_ROOT%
  pause
  exit /b 1
)
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PACKAGE_ROOT%Launch_PathPocket.ps1"
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
