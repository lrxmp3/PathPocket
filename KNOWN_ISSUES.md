# Known issues and unverified areas

This is a private pre-release preparation record for PathPocket v1.0.6.

## Windows 11 / WSL2

- The R1 external run completed installation, verification, shortcut launch, HSA (20 molecules), 7KWZ (20 molecules), and the GUI NO_TARGETS control (0 selected targets, 0 ED2Mol calls, 0 molecules); HSA also ran normally afterward.
- In that same R1 run, the GUI buttons for opening Chinese/English reports returned exit code 1 when `explorer.exe` was asked to open a Linux file path. The report files themselves were valid and accessible through the `\\wsl.localhost\Ubuntu-24.04\...` path.
- The current source changes file opening to `rundll32.exe url.dll,FileProtocolHandler` for files while retaining `explorer.exe` for directories. File-opening unit tests and final-package preflight pass, but a new Windows external run of the rebuilt package is **not tested**. If a report button still fails, open the generated report through `\\wsl.localhost\Ubuntu-24.04\...` in Windows Explorer.
- Fresh-machine WSL branches A/B/C/E, clean Ubuntu without preinstalled bzip2, restart/reopen of historical projects, and complex-export inspection remain **not tested** for the rebuilt candidate.

## Direct Linux

- Historical Ubuntu 22.04.5/RTX 3080 Ti evidence validated installation, doctor, HSA, 7KWZ and complex export for an older v1.0.6 package. Its NO_TARGETS run failed (3 targets and 60 molecules), so it is not candidate acceptance evidence.
- A later repair record reports automated final-package Linux checks, but the package predates the current Windows native-output integration and file-opening change. Fresh direct-Linux installation and complete GUI acceptance of the rebuilt candidate remain **not tested**.
- Ubuntu 24.04 direct installation, manual report/SDF opening, SDF association behavior, and third-party viewer inspection remain **not tested**.

## Release/legal boundary

- PathPocket-owned source is recorded as MIT, copyright 李瑞熙.
- ED2Mol v1.1 weights and the locked `smina.static` are downloaded from upstream rather than redistributed inside the installer. Their external-asset license scope still needs explicit rightsholder confirmation; download-on-install does not itself settle that question.
