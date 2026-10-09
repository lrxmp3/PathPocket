# Windows 11 / WSL2 candidate validation

| Check | R1 result | Rebuilt current candidate |
| --- | --- | --- |
| WSL D_READY UTF-16LE detection | PASS | Source integrated; package retest pending |
| Setup / Verify (17 checks) / shortcut | PASS | NOT TESTED |
| GUI v1.0.6 | PASS | NOT TESTED |
| HSA / 7KWZ | PASS, 20 molecules each | NOT TESTED |
| GUI NO_TARGETS | PASS: 0 targets, 0 ED2Mol calls, 0 molecules | NOT TESTED |
| HSA after NO_TARGETS | PASS | NOT TESTED |
| Direct report buttons | FAIL (exit 1) | Source fix unit-tested; external retest pending |
| A/B/C/E WSL states, clean bzip2-free Ubuntu | NOT TESTED | NOT TESTED |
| Restart/history reopen, complex viewer inspection | NOT TESTED | NOT TESTED |

R1 ran on Windows 11 with Ubuntu 24.04/WSL2 and a working WSL-visible NVIDIA GPU. The current candidate changes only the file-opening route after R1; old R1 evidence is retained as provenance and is not relabelled as a pass for a rebuilt ZIP.
