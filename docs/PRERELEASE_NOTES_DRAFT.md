# Draft — PathPocket v1.0.6 — Linux / Windows (WSL2)

**Status: private draft only. Do not publish or mark latest/stable.**

This candidate preserves the paper-facing PathPocket v1.0.6 GUI, workflow, report templates and scientific parameters. It provides direct Linux installation and Windows 11 installation through Ubuntu 24.04 on WSL2/WSLg. Windows is not a native scientific implementation; both routes use the same Linux core.

Included maintenance fixes: the trusted built-in NO_TARGETS fixture selects zero targets at the target-selection boundary and completes without ED2Mol calls or molecules; ordinary projects remain unaffected. Windows setup correctly decodes UTF-16LE `wsl.exe` output and does not reconvert an already-ready WSL2 distribution. WSL file and directory opening use environment-appropriate Windows calls.

Release assets: `PathPocket-v1.0.6-source.tar.gz`, `PathPocket_v1.0.6_Linux.tar.gz`, `PathPocket_v1.0.6_Windows.zip`, `SHA256SUMS.txt`, English and Chinese installation guides, and these release notes. Final hashes and source SHA are generated only after the final merge and reproducible rebuild.

Known issues and untested items are listed in `KNOWN_ISSUES.md` and the platform validation records. In particular, the externally validated R1 package's direct report buttons failed, although the report files were valid and opened through `\\wsl.localhost\Ubuntu-24.04\...`. The candidate includes a focused file-opening repair with unit-test and package-preflight coverage; the repaired button still needs external Windows retesting. Fresh-machine WSL branches A/B/C/E, clean Ubuntu without bzip2, GUI history restoration and complex-export inspection remain untested. Direct-Linux installation/doctor/GUI startup passed for the candidate; its scientific examples reuse the previously accepted core and were not rerun solely for documentation and licensing changes.

PathPocket-owned source is MIT licensed, copyright 李瑞熙. ED2Mol v1.1 weights and the locked `smina.static` are downloaded from their upstream locations and are not bundled in the installers; explicit confirmation of the license scope for those external binary assets remains pending.
