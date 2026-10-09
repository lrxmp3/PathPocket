@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "WSL_EXE=%SystemRoot%\System32\wsl.exe"
if not exist "%WSL_EXE%" (
  echo [ERROR] wsl.exe was not found: %WSL_EXE%
  pause
  exit /b 1
)
"%WSL_EXE%" -d Ubuntu-24.04 --exec bash -lc "root=$(cat \"$HOME/.pathpocket_hf5_install_root\" 2>/dev/null); test -n \"$root\" && cd \"$root\" && bash Verify_Installation.sh --quick"
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%
