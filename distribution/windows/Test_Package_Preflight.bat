@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PACKAGE_ROOT=%~dp0"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL_EXE%" (
  echo [ERROR] The system Windows PowerShell executable was not found: %POWERSHELL_EXE%
  if not defined PATHPOCKET_NO_PAUSE pause
  exit /b 1
)
pushd "%PACKAGE_ROOT%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Cannot enter the extracted package directory: %PACKAGE_ROOT%
  if not defined PATHPOCKET_NO_PAUSE pause
  exit /b 1
)
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PACKAGE_ROOT%Test_Package_Preflight.ps1"
set "RC=%ERRORLEVEL%"
popd
echo.
if "%RC%"=="0" echo Package preflight: PASS
if not "%RC%"=="0" echo Package preflight: FAIL. Keep the diagnostics folder.
if not defined PATHPOCKET_NO_PAUSE pause
exit /b %RC%
