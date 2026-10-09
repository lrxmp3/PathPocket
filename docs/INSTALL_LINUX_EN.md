# Direct Linux installation

1. Obtain the approved `.tar.gz` asset and verify the SHA256 of the archive against `SHA256SUMS.txt`.
2. Install a compatible host NVIDIA driver. Do not let PathPocket replace the driver or an existing Conda/GROMACS environment.
3. Extract the archive to a writable folder. A path containing spaces is supported. Preserve executable bits and symlinks; if a transfer tool removed them, run `chmod +x Setup_First_Run.sh PathPocket.sh Verify_Installation.sh Verify_Package.sh Create_Shortcuts.sh`.
4. From the extracted package root run `./Verify_Package.sh`, then `./Setup_First_Run.sh`. Internet access is required for the locked runtime dependencies, fpocket and official ED2Mol weights.
5. Run `./Verify_Installation.sh`. Continue to new generation only after all required doctor checks pass.
6. Launch with `./PathPocket.sh`; optionally run `./Create_Shortcuts.sh`. Keep projects outside the installation directory.

The GUI must display v1.0.6. Preserve install/doctor logs and exit codes after any failure. The source repository is not the portable installer. The current candidate still needs a fresh native-Linux install and GUI workflow acceptance; older Linux evidence cannot substitute for it. See `KNOWN_ISSUES.md`.
