# Windows 11 installation through WSL2

PathPocket is not a native Windows compute program. This package installs and launches the common Linux core in Ubuntu 24.04 on WSL2/WSLg.

1. Verify the SHA256 of the **original ZIP before extraction** against `SHA256SUMS.txt`.
2. Extract the complete ZIP to a writable folder. Spaces and Unicode characters are supported. Do not run scripts from inside the ZIP viewer.
3. Double-click `Test_Package_Preflight.bat`. Continue only after `Package preflight: PASS`.
4. Double-click `Setup_First_Run.bat`. It may request elevation to run `wsl.exe --install -d Ubuntu-24.04`. If it reports `RESTART_REQUIRED`, restart Windows, open Ubuntu once to create its Linux user/password, and rerun the same setup script.
5. Setup downloads locked dependencies, fpocket and ED2Mol weights from the URLs recorded in the nested Linux package. Internet access is required. It does not install Linux or Windows NVIDIA drivers and does not alter Conda/base or GROMACS environments.
6. Run `Verify_Installation.bat`, then `Create_Desktop_Shortcut.bat`. Launch PathPocket from the shortcut created by the latter, or run `Launch_PathPocket.bat`.
7. Keep projects outside the installation folder. The GUI must display v1.0.6.

For failures, preserve the `diagnostics` folder, screenshot, exact exit code and reproduction steps. A file-opening failure does not prove the report or SDF is missing: confirm the file in the run directory and record whether Windows has an application associated with SDF files. See `KNOWN_ISSUES.md` for the candidate's validation limits.

GPU detection uses `wsl -d Ubuntu-24.04 -- nvidia-smi` (or the official WSL shim). Install only a compatible Windows NVIDIA driver. Never install a separate Linux NVIDIA display driver inside WSL.
