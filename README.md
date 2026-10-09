# PathPocket

Compare corresponding protein microregions across conformations or repeats, generate candidates with pretrained ED2Mol, and inspect chemical space with source-linked coordinate export.

## What it does
Groups local regions by geometry and canonical residue identity; retains state/repeat context; records target, molecule and source-file provenance. It does not retrain ED2Mol, establish binding, or convert Qnorm into affinity.

## Choose your starting point
- **No GPU:** open the precomputed HSA replay. Browse molecules, chemical space and 3D context, then export a complex.
- **With a supported NVIDIA GPU:** use the installed scientific runtime and the one-target, ten-molecule HSA minimal example.
- **First-time portable users:** follow the Windows/Linux installation guide; the source archive is separate from a binary installer.

## Runtime architecture and installation

PathPocket has one Linux scientific core and two installation routes: direct Linux installation, and Windows 11 installation through Ubuntu 24.04 on WSL2/WSLg. The Windows package is **not a native Windows scientific executable**. Windows scripts provision and launch the same Linux core, and translate file-opening requests to Windows where appropriate.

Python ≥3.11 is required for source use and PySide6 6.8.3 for the GUI. New generation also needs a compatible NVIDIA driver, the pinned CUDA/PyTorch environment, fpocket, and the official ED2Mol weights. Install source with `python -m pip install .`; viewer dependencies with `python -m pip install -r requirements-viewer.txt`. Portable installation uses an isolated runtime and does not modify the user's Conda base environment. [Windows 11 + WSL2 guide](docs/INSTALL_WINDOWS_EN.md) · [Direct Linux guide](docs/INSTALL_LINUX_EN.md).

## Quick start
Read the [illustrated tutorial](docs/PathPocket_Tutorial_EN.md). In the installed GUI open the replay's historical run. Select RF_0011_state_B → Molecules → a molecule → Structure Location → Export. Source users can run `python scripts/replay.py <run-directory>`.

## Examples, tests and outputs
`examples/HSA_MINIMAL_10` contains prepared public HSA inputs and a ten-molecule contract. `examples/fixtures` contains HSA, 7KWZ and NO_TARGETS examples. Run `python -m pytest tests` for unit contracts; no generation is needed for these tests. Full paper data and replay are separate from GitHub source staging. Outputs include run_manifest.json, region/target tables, SDF, QC/chemical-space CSVs and coordinate-preserving PDB/SDF/JSON exports.

## Validation status and known limits

The maintained candidate preserves the paper-facing v1.0.6 GUI, workflow, report templates and scientific parameters. Historical Ubuntu 22.04/RTX 3080 Ti evidence validates an earlier Linux package but also records its unfixed NO_TARGETS failure; it is not acceptance evidence for the new candidate. Windows 11/WSL2 R1 evidence validates installation and the principal HSA, 7KWZ and NO_TARGETS workflows, but its direct report buttons failed. The source candidate contains a targeted Windows file-opening repair that still requires fresh external validation. See [known issues](KNOWN_ISSUES.md) and the platform validation records.

## Citation and licensing

PathPocket-owned source and documentation are released under the [MIT License](LICENSE), copyright 李瑞熙. Third-party software, fonts, data and model assets keep their own terms; the root license does not relicense them. If you use PathPocket, cite this software and, after publication, the accompanying paper. Bibliographic fields and a DOI that are not yet known are intentionally not invented. See [third-party notices](THIRD_PARTY_NOTICES.md), the retained texts under `LICENSES/`, and `third_party/README.md`. [中文说明](README_zh-CN.md).
