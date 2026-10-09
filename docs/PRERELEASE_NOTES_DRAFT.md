# Draft — PathPocket v1.0.6 — Linux / Windows (WSL2)

**Status: private draft only. Do not publish or mark latest/stable.**

This candidate preserves the paper-facing PathPocket v1.0.6 GUI, workflow, report templates and scientific parameters. It provides direct Linux installation and Windows 11 installation through Ubuntu 24.04 on WSL2/WSLg. Windows is not a native scientific implementation; both routes use the same Linux core.

Included maintenance fixes: the trusted built-in NO_TARGETS fixture selects zero targets at the target-selection boundary and completes without ED2Mol calls or molecules; ordinary projects remain unaffected. Windows setup correctly decodes UTF-16LE `wsl.exe` output and does not reconvert an already-ready WSL2 distribution. WSL file and directory opening use environment-appropriate Windows calls.

Release assets planned: `PathPocket_v1.0.6_Linux.tar.gz`, `PathPocket_v1.0.6_Windows.zip`, `SHA256SUMS.txt`, both installation guides, and dual-route release notes. Final names, hashes and source SHA must be filled only after reproducible rebuild and package preflight.

Known issues and untested items are listed in `KNOWN_ISSUES.md` and the platform validation records. In particular, R1 report buttons failed; the source fix needs external retesting. Direct-Linux candidate installation and several clean-Windows WSL states remain untested. Public release is also blocked on rightsholder confirmation of the root license/copyright and remaining third-party redistribution evidence.
