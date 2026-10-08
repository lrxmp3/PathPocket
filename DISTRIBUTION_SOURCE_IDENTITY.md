# Distribution source identity

This source snapshot corresponds to the PathPocket v1.0.6 dual-platform repair build dated 2026-10-06.

## Frozen scientific identities

- PathPocket GUI/distribution: 1.0.6
- Fast Screening Baseline: 1.0
- Backend: 0.3.0, commit `f2e5d7ffd49d8e3546d6841337b4f68b58f0abd3`
- ED2Mol: commit `09f133da913179f82b285dbb046f1ecb81d1da37`
- Publication helper: commit `40c5b2fa79254227d7f4ca28cb09298f31d784b5`

The maintained v1.0.6 source history is based on commit `3de45d20e7ca7952a968a0ba709309a134a452d0`. The later report/SDF cross-platform opening repair was reconstructed and verified by file hash from the shared runtime; no trustworthy additional Git commit was available, so the exact GUI file hashes in `distribution/linux/release_manifest.json` are authoritative for this repair build.

## Layout

- `src/`: scientific backend source.
- `gui/`: GUI source matching the shared Linux/WSL runtime.
- `tests/`: backend, NO_TARGETS GUI, molecule-rendering, shortcut, report and SDF path tests.
- `distribution/linux/`: Linux installer/build scripts and locked acquisition metadata.
- `distribution/windows/`: Windows 11/WSL2 installer and launcher sources.

The installable Linux and Windows archives are separate release assets. This source archive is not itself an installer and does not bundle a runtime or model weights.

## Scope

The maintenance changes cover the trusted GUI NO_TARGETS path, paths containing spaces, automatic 2D molecule rendering, and cross-platform opening of reports, result folders and SDF files. Scientific algorithms, model weights, thresholds, generation parameters, random seeds and report definitions are unchanged. No v1.0.7 interface redesign or FLAME code is included.
