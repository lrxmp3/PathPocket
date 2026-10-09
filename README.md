# PathPocket

PathPocket is a desktop workflow for comparing corresponding protein microregions across conformations or repeated units, selecting representative targets, generating candidate molecules with pretrained ED2Mol, and inspecting the resulting chemical and structural space.

This repository contains the first public release of PathPocket, version 1.0.6.

[中文说明](README_zh-CN.md)

## Main features

- Match local protein regions using geometry and canonical residue identity while retaining conformation, state, and repeat context.
- Run candidate generation through the packaged scientific workflow and keep target, molecule, source-file, and parameter provenance.
- Browse generated molecules as two-dimensional structures and explore their chemical-space relationships.
- Locate candidates in the source protein structure and export coordinate-preserving PDB, SDF, JSON, CSV, and report files.
- Reopen completed runs for inspection and reproducibility.

PathPocket does not retrain ED2Mol, and generated candidates are not experimental evidence of binding. Qnorm is a workflow score, not a binding-affinity measurement.

## Supported installation routes

PathPocket supports:

- **Direct installation on Linux** using the Linux release package.
- **Installation and operation on Windows 11 through WSL2**, using Ubuntu 24.04 and WSLg. Windows and Linux use the same Linux scientific core; the Windows package provides the WSL2 installation, launch, shortcut, and file-opening integration.

New molecule generation requires a compatible NVIDIA GPU and driver together with the pinned CUDA/PyTorch environment, fpocket, and official ED2Mol assets. The packaged installers use an isolated runtime and do not modify the user's Conda base environment.

Download the appropriate package from the [v1.0.6 release](https://github.com/lrxmp3/PathPocket/releases/tag/v1.0.6), verify it with `SHA256SUMS.txt`, and follow the platform guide:

- [Linux installation guide](docs/INSTALL_LINUX_EN.md)
- [Windows 11 / WSL2 installation guide](docs/INSTALL_WINDOWS_EN.md)
- [Linux 安装指南](docs/INSTALL_LINUX_ZH.md)
- [Windows 11 / WSL2 安装指南](docs/INSTALL_WINDOWS_ZH.md)

For source-based inspection or development, Python 3.11 or newer is required. Install the Python package with `python -m pip install .`; optional viewer dependencies are listed in `requirements-viewer.txt`.

## Quick start

1. Install PathPocket with the guide for your platform and run the bundled installation verifier.
2. Start the v1.0.6 GUI from the installed launcher or desktop shortcut.
3. Choose a writable project directory outside the application directory.
4. Open one of the supplied examples, confirm its prepared settings, and start the run.
5. Inspect regions, selected targets, molecules, chemical space, reports, and exported files from the **Results** page.

The [illustrated tutorial](docs/PathPocket_Tutorial_EN.md) and [中文图文教程](docs/PathPocket_Tutorial_ZH.md) provide a complete guided workflow.

## Examples

- **Conventional HSA** demonstrates the standard protein-region and candidate-generation workflow.
- **Repeat Aggregate 7KWZ** demonstrates region correspondence and molecule placement for a repeated/aggregate structure.
- **NO_TARGETS** is a normal engineering test case for the zero-selected-target path. It completes without invoking ED2Mol or generating molecules.
- `examples/HSA_MINIMAL_10` provides a compact prepared HSA input and expected ten-molecule contract for GPU-enabled checks.

The repository's unit and workflow contracts can be run with `python -m pytest tests`. Example generation may vary across supported GPU environments; compare the documented result contract rather than expecting identical molecular file hashes.

## Validation

Release testing covered installation and the principal HSA, 7KWZ, and NO_TARGETS workflows on direct Linux and on Windows 11 through WSL2. The recorded environments and the exact scope of each check are documented in [Linux validation](docs/VALIDATION_LINUX.md), [Windows/WSL2 validation](docs/VALIDATION_WINDOWS_WSL2.md), and the [validation summary](docs/VALIDATION_STATUS_2026-10-08.md). These results apply to the recorded configurations and do not imply validation on every Linux distribution, Windows configuration, GPU, or external viewer.

For the report-opening limitation and checks that still require external retesting, see [Known issues](KNOWN_ISSUES.md).

## Citation

If you use PathPocket, cite the software release. Please also cite the accompanying paper after its bibliographic information becomes available. The repository's machine-readable citation metadata is provided in [`CITATION.cff`](CITATION.cff); unknown DOI and paper fields are intentionally left unset rather than inferred.

## License and third-party software

PathPocket-owned source code and documentation are released under the [MIT License](LICENSE), copyright 李瑞熙. Third-party software, fonts, data, model assets, and downloaded runtime components remain under their respective terms and are not relicensed by the PathPocket license.

See [contributors](AUTHORS.md), [third-party notices](THIRD_PARTY_NOTICES.md), the original license texts under [`LICENSES/`](LICENSES/), and [`third_party/README.md`](third_party/README.md).
