# Windows/WSL2 installer remediation — 2026-10-09

This source branch records the v1.0.6 Windows/WSL2 installer remediation. It is not a substitute for the separately built, hash-recorded external-test ZIP. The GUI display version remains v1.0.6.

## Scope

- Detect WSL states A (absent), B (Ubuntu absent), C (Ubuntu WSL1), D (ready), and E (Ubuntu first user uninitialized).
- Log official WSL installation/conversion output and return a normal continuation status when a reboot or Ubuntu first-user setup is required.
- Probe `nvidia-smi` first, then the official WSL shim at `/usr/lib/wsl/lib/nvidia-smi`; do not modify drivers or PATH.
- Avoid a clean-Ubuntu `bzip2` dependency by using a packaged Python-only safe extractor after micromamba archive hash verification.
- Open WSLg result files through `wslpath -w` and Windows Explorer without shell-string interpolation.
- Report only the verified builtin NO_TARGETS fixture as a forced-empty engineering control after normal candidate discovery and matching. Natural zero-target reports remain unchanged.

## Explicit non-scope

The remediation does not change PathPocket scientific algorithms, normal target selection, ED2Mol, model weights, seeds, generation parameters, HSA/7KWZ examples, GUI layout/theme/buttons, or report structure. It does not publish a release, upload artifacts, install drivers, or alter users' existing Conda/GROMACS environments.

## Validation

Source tests cover the report branches, WSL-to-Windows opening argument construction, static installer contracts, and safe bzip2 extraction behavior. A clean Windows 11 external run remains required for PowerShell/UAC, WSL/reboot continuation, GPU, WSLg, desktop shortcut, GUI clicks, HSA, 7KWZ, and NO_TARGETS acceptance.
