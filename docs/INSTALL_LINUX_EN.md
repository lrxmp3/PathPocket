# Direct Linux installation

1. Obtain the approved `.tar.gz` asset and verify the SHA256 of the archive against `SHA256SUMS.txt`.
2. Install a compatible host NVIDIA driver. Do not let PathPocket replace the driver or an existing Conda/GROMACS environment.
3. Extract the archive to a writable folder. Linux path compatibility has not been established for all installation and project paths; see `KNOWN_ISSUES.md` for the observed fpocket limitations with spaces and long input paths. Preserve executable bits and symlinks; if a transfer tool removed them, run `chmod +x Setup_First_Run.sh PathPocket.sh Verify_Installation.sh Verify_Package.sh Create_Shortcuts.sh`.
4. Run `./Verify_Package.sh` and then `./Setup_First_Run.sh` from the package root. Setup downloads hash-locked ED2Mol weights, smina, fpocket, and runtime dependencies from their configured sources. Internet access is required. The weights and smina license scope remains unresolved; a matching SHA256 does not establish authorization.
5. Run `./Verify_Installation.sh`. Continue to new generation only after all required doctor checks pass.
6. Launch with `./PathPocket.sh`; optionally run `./Create_Shortcuts.sh`. Keep projects outside the installation directory.

The GUI must display v1.0.7. Preserve install/doctor logs and exit codes after any failure. The source repository is not the portable installer. The current candidate still needs a fresh native-Linux install and GUI workflow acceptance; older Linux evidence cannot substitute for it. See `KNOWN_ISSUES.md`.
