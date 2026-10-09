# Distribution source identity

This source snapshot is the PathPocket v1.0.6 Linux / Windows (WSL2) repair candidate prepared on 2026-10-09. Both installation routes use the same Linux scientific core; Windows is not a native scientific implementation.

## Frozen scientific identities

- PathPocket GUI/distribution: 1.0.6
- Fast Screening Baseline: 1.0
- Backend: 0.3.0, commit `f2e5d7ffd49d8e3546d6841337b4f68b58f0abd3`
- ED2Mol: commit `09f133da913179f82b285dbb046f1ecb81d1da37`
- Publication helper: commit `40c5b2fa79254227d7f4ca28cb09298f31d784b5`

The maintained v1.0.6 source history is based on commit `3de45d20e7ca7952a968a0ba709309a134a452d0`. Windows installer build `d616f58b4b7c698e03b627a67e7923ef0c93ef2b` was supplied as a hash-recorded source diff and final package, but its Git object is not present in this repository. Its WSL UTF-16LE/native-output fix was therefore integrated from that preserved evidence rather than represented as a cherry-pick. The integration commit and both rebuilt installer hashes are recorded separately after the private-branch commit.

## Layout

- `src/`: scientific backend source.
- `gui/`: GUI source matching the shared Linux/WSL runtime.
- `tests/`: backend, NO_TARGETS GUI, molecule-rendering, shortcut, report and SDF path tests.
- `distribution/linux/`: Linux installer/build scripts and locked acquisition metadata.
- `distribution/windows/`: Windows 11/WSL2 provisioning, launcher and shortcut sources.

The installable Linux and Windows/WSL2 archives are separate release assets. This source archive is not itself an installer and does not bundle a preinstalled runtime or model weights.

## Scope

The maintenance changes cover the trusted GUI NO_TARGETS path, paths containing spaces, automatic 2D molecule rendering, and cross-platform opening of reports, result folders and SDF files. Scientific algorithms, model weights, thresholds, generation parameters, random seeds and report definitions are unchanged. No v1.0.7 interface redesign or FLAME code is included.
