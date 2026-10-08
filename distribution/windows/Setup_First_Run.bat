@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup_First_Run.ps1"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="20" echo WSL installation was requested. Restart Windows if prompted, finish Ubuntu first launch, then run this file again.
if "%RC%"=="30" echo WSL2 is ready but the NVIDIA GPU is unavailable inside WSL. Do not install a Linux NVIDIA driver.
if not "%RC%"=="0" if not "%RC%"=="20" echo Installation did not complete. Keep this window and the diagnostics folder.
pause
exit /b %RC%
