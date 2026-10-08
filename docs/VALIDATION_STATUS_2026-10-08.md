# PathPocket v1.0.6 repair — validation status (2026-10-08)

This record documents the validation completed against the final Linux
distribution candidate.  It is a test-status record, not a public release
announcement and not evidence that every supported platform has been
independently accepted.

## Distribution under test

| Item | Value |
| --- | --- |
| GUI display version | `v1.0.6` |
| Linux archive | `PathPocket_v1.0.6_Linux_x64_GPU_Repair_20261006.tar.gz` |
| Archive SHA256 | `21a9198534bb3942a986ba697ace93c38f136e55fa80c61a101e47ded90c2a4b` |
| Distribution source identity reported by the run manifest | `f2e5d7ffd49d8e3546d6841337b4f68b58f0abd3` |
| NO_TARGETS fixture | `builtin_no_targets_v1` — force empty selection only after normal discovery and matching |

The candidate was freshly extracted into an isolated path containing both
Chinese characters and spaces.  First-run installation, its bundled package
verification, and GUI startup all used that extracted copy.  Existing
installations and historical projects were not used as the runtime or result
source.

## Test environment

| Item | Observed value |
| --- | --- |
| Host | native Linux desktop, GNOME/X11 |
| OS | Ubuntu 22.04.5 LTS |
| GPU | NVIDIA GeForce RTX 3080 Ti |
| NVIDIA driver | 580.65.06 |
| Runtime | bundled Python 3.11.16, PyTorch 2.14.0+cu130, CUDA 13.0 |

The published Linux guide targets Ubuntu 24.04 LTS.  The successful Ubuntu
22.04.5 run is useful compatibility evidence, but **does not replace an
independent Ubuntu 24.04 acceptance test**.

## Completed tests

| Check | Result | Evidence summary |
| --- | --- | --- |
| Archive checksum and fresh extraction | PASS | SHA256 matched the distribution manifest; bundled `Verify_Package.sh` passed. |
| First-run installation and doctor | PASS | Bundled runtime, GPU, CUDA tensor, ED2Mol import/weights, fpocket and locked hashes all passed. |
| Formal GUI launcher | PASS | `PathPocket.sh` opened a visible window titled `PathPocket v1.0.6`; isolated GUI doctor passed. |
| Unicode and space paths | PASS | Installation, GUI startup, HSA, 7KWZ and NO_TARGETS workspaces used Chinese-and-space paths. |
| Package automated tests | PASS | 9/9 bundled tests passed, including path conversion, report URL encoding, SDF association handling and Windows-open routing unit checks. |
| HSA smoke workflow | PASS | One selected target; ED2Mol exit code 0; 10 requested/generated/valid/unique molecules; 9 physical-compatible; HTML/Markdown report and SDF produced. |
| 7KWZ smoke workflow | PASS | One selected target; ED2Mol exit code 0; 10 requested/generated/valid/unique molecules; 6 physical-compatible; reports, figures, SDF and QC acceptance record produced. |
| NO_TARGETS GUI execution chain | PASS (automated GUI) | Final-package `Window.open_demo()` followed by the original `run_clicked()` created one new project/run.  Normal discovery found 30 instances and matching found 27 families; target selection was then forced empty by the bound built-in fixture.  The run completed as `NO_TARGETS`, target count 0, generated count 0, ED2Mol invocation count 0, and the report/result page loaded. |
| HSA result presentation | PASS (automated GUI) | Final-package GUI loaded the completed HSA run: 10 molecules, 10/10 rendered 2-D SVG structures, 10 gallery widgets, bilingual HTML presentation, and 10 matching 3-D SDF records. |

The NO_TARGETS result is an engineering zero-target control.  It does not
claim that its input proteins lack pockets: discovery and matching evidence is
intentionally retained before the fixture applies the empty target selection.

## Important limits / still required

The following are **not tested** and must not be described as PASS:

- A fresh Windows 11 installation with no pre-existing WSL, including the
  WSL2/Ubuntu bootstrap and desktop shortcut path.
- An independent Ubuntu 24.04 desktop installation.
- Human mouse-click acceptance through every GUI operation.  The GUI tests
  above exercise the installed GUI methods and visible window automatically;
  they do not replace a manual GUI session.
- External application behaviour after manually clicking Open Report, Open
  SDF, Open Folder, or complex export, including the presence of an SDF viewer
  association on the receiving computer.
- Protein–ligand complex export inspection in a third-party molecule viewer.

## Publication boundary

Only source and documentation belong in this private GitHub repository at
this point.  The Linux/Windows installer archives, model/third-party
redistribution review, and any GitHub Release or Zenodo upload remain pending
the outstanding external validation and redistribution checks.
