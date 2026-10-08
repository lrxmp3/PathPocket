# PathPocket

Compare corresponding protein microregions across conformations or repeats, generate candidates with pretrained ED2Mol, and inspect chemical space with source-linked coordinate export.

## What it does
Groups local regions by geometry and canonical residue identity; retains state/repeat context; records target, molecule and source-file provenance. It does not retrain ED2Mol, establish binding, or convert Qnorm into affinity.

## Choose your starting point
- **No GPU:** open the precomputed HSA replay. Browse molecules, chemical space and 3D context, then export a complex.
- **With a supported NVIDIA GPU:** use the installed scientific runtime and the one-target, ten-molecule HSA minimal example.
- **First-time portable users:** follow the Windows/Linux installation guide; the source archive is separate from a binary installer.

## Requirements and installation
Python ≥3.11 for source use; PySide6 6.8.3 for the viewer. New generation needs the tested CUDA/NVIDIA runtime, official ED2Mol weights and fpocket. Install source with `python -m pip install .`; viewer dependencies with `python -m pip install -r requirements-viewer.txt`. Portable scientific installation uses a private runtime. [Windows guide](docs/INSTALL_WINDOWS_EN.md) · [Linux guide](docs/INSTALL_LINUX_EN.md).

## Quick start
Read the [illustrated tutorial](docs/PathPocket_Tutorial_EN.md). In the installed GUI open the replay's historical run. Select RF_0011_state_B → Molecules → a molecule → Structure Location → Export. Source users can run `python scripts/replay.py <run-directory>`.

## Examples, tests and outputs
`examples/HSA_MINIMAL_10` contains prepared public HSA inputs and a ten-molecule contract. `examples/fixtures` contains HSA, 7KWZ and NO_TARGETS examples. Run `python -m pytest tests` for unit contracts; no generation is needed for these tests. Full paper data and replay are separate from GitHub source staging. Outputs include run_manifest.json, region/target tables, SDF, QC/chemical-space CSVs and coordinate-preserving PDB/SDF/JSON exports.

## Citation and license
See `CITATION.cff`; author details and the software DOI are pending final approval. The source license must be approved before this repository is made public. Third-party components retain their own terms; see `THIRD_PARTY_NOTICES.md` and `third_party/README.md`. [中文说明](README_zh-CN.md).
