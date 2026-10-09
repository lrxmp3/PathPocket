# Known issues and unverified areas

This document records the known limitations of the PathPocket v1.0.6 Pre-release. It does not change the scientific workflow or the generated result files.

## Windows 11 / WSL2 report opening

- In an external Windows 11/Ubuntu 24.04 WSL2 run, PathPocket generated valid Chinese and English report files, but the GUI report-open buttons returned exit code 1 when the Windows opener received a Linux path.
- The current package routes file opening through the Windows file protocol handler. Unit tests and final-package preflight checks pass, but the repaired GUI action has **not yet received a fresh external-machine retest**.
- If the button does not open a report, open Windows Explorer and enter the report's WSL network path, for example `\\wsl.localhost\Ubuntu-24.04\...`. This is a workaround for opening an existing report; it does not repair a missing report file.
- If an SDF file exists but does not open, confirm that Windows has an SDF-compatible viewer associated with the file type. A missing association is different from an export failure.

## Unverified configurations

- Fresh-machine WSL setup branches involving initial Windows restart and Ubuntu first-user initialization have not all been retested with the current package.
- Restart-and-reopen of historical projects and manual inspection of every complex-export field remain unverified on the current Windows/WSL2 package.
- Validation does not cover every Linux distribution, desktop environment, GPU/driver combination, WSL configuration, or third-party molecular viewer.

## External assets

- ED2Mol model assets and the locked `smina.static` binary are obtained from their upstream sources during installation rather than redistributed in the release package. Their terms remain separate from the PathPocket MIT license; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [`third_party/README.md`](third_party/README.md).
