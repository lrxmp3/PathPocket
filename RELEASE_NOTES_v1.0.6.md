# PathPocket v1.0.6 — First Public Release

PathPocket v1.0.6 is the first public release of the PathPocket protein-microregion chemical-space workflow. It provides one Linux scientific core through two supported installation routes: direct Linux installation and Windows 11 installation and operation through Ubuntu 24.04 on WSL2/WSLg.

This release remains a **Pre-release** while the remaining external file-opening retest and documented unverified configurations are completed.

## Feature overview

- Compare corresponding protein microregions across conformations, states, or repeated units.
- Select representative targets and generate candidate molecules with pretrained ED2Mol.
- Preserve target, molecule, input-file, coordinate, and parameter provenance.
- Browse two-dimensional molecular structures, chemical-space plots, protein context, bilingual reports, and exported result files.
- Reopen completed runs and export coordinate-preserving PDB, SDF, JSON, and CSV records.
- Use the supplied HSA, 7KWZ, and NO_TARGETS examples to exercise standard, repeat/aggregate, and zero-selected-target workflows.

Generated candidates are not experimental evidence of binding, and Qnorm is not a binding-affinity measurement.

## Download and installation

Release assets include:

- `PathPocket_v1.0.6_Linux.tar.gz` — direct Linux installer.
- `PathPocket_v1.0.6_Windows.zip` — Windows 11 installer for the WSL2-hosted Linux core.
- `PathPocket-v1.0.6-source.tar.gz` — corresponding source archive.
- `SHA256SUMS.txt` — checksums for release files.
- English and Chinese installation guides for both installation routes.

Verify the downloaded package before extraction, then follow the corresponding guide:

- [Direct Linux installation](docs/INSTALL_LINUX_EN.md)
- [Windows 11 / WSL2 installation](docs/INSTALL_WINDOWS_EN.md)

Windows uses WSL2 and WSLg; this is not a native Windows scientific executable. New molecule generation requires a compatible NVIDIA GPU environment and the scientific dependencies described in the installation guides.

## Validation summary

Release evidence covers installation and the principal HSA, 7KWZ, and NO_TARGETS workflows on direct Linux and on Windows 11 through WSL2. The Windows/WSL2 evidence also covers shortcut launch, GPU visibility, and a normal HSA run after NO_TARGETS. Automated package and source checks cover installer contracts, path handling, report/SDF routing, molecule rendering, and the zero-target completion path.

Validation applies to the recorded systems and checks only; it does not claim coverage of every Linux distribution, Windows/WSL2 state, GPU, viewer, or desktop configuration. See the platform validation records for the exact scope.

## Known issues

An external Windows/WSL2 run produced valid Chinese and English report files, but the direct GUI report-open action failed for the Linux path. The current package contains a focused file-opening repair that passed unit and package-preflight checks; fresh external retesting of that repaired button remains pending. Until confirmed, reports can be opened from Windows Explorer through `\\wsl.localhost\Ubuntu-24.04\...`.

Additional unverified configurations are listed in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## License and citation

PathPocket-owned source code and documentation are released under the [MIT License](LICENSE), copyright 李瑞熙. Third-party software, data, model assets, and runtime components retain their own licenses and notices; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [`LICENSES/`](LICENSES/).

Please cite this software release when using PathPocket. The paper citation and software DOI will be added when their final bibliographic information is available; no provisional DOI or unpublished citation is asserted here.
