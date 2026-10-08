@echo off
setlocal
wsl.exe -d Ubuntu-24.04 --exec bash -lc "root=$(cat \"$HOME/.pathpocket_hf5_install_root\" 2>/dev/null); cd \"$root\" && bash Verify_Installation.sh --quick"
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%
