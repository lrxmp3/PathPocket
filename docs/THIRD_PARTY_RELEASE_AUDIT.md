# Third-party release audit — open items

The source repository does not contain a preinstalled runtime or model weights. The installers use locked URLs and hashes; this design improves reproducibility but does not itself grant redistribution or download rights.

| Component | Version/source evidence | Delivery model | License evidence | Open action |
| --- | --- | --- | --- | --- |
| ED2Mol source | commit `09f133da913179f82b285dbb046f1ecb81d1da37`; per-file hashes in `third_party/engine-source-hashes.json` | Source included in installer template | Upstream MIT notice preserved | Confirm source/fragment assets covered; retain notice |
| ED2Mol weights | upstream v1.1 `weights.zip`, locked SHA256 | Download on first install; not in source repo | No separate weight license captured | Obtain explicit weight terms/permission before public installer |
| PySide6 Essentials | 6.8.3 | Downloaded locked wheel | lock records LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | Preserve notices and verify LGPL distribution obligations |
| PyTorch | 2.14.0+cu130 | Downloaded locked wheel | composite license metadata recorded | Preserve bundled notices delivered by wheel |
| NVIDIA/CUDA Python packages | CUDA 13 family, exact URLs/hashes in lock | Downloaded during install; no display driver bundled | nine proprietary entries; several license fields unspecified | Verify NVIDIA/PyPI terms and user notice; do not bundle a driver |
| fpocket | locked installer acquisition | Download/install | Evidence needs extraction from actual lock/package | Capture upstream version, license text and installed files |
| RDKit/Biopython/scientific Python stack | exact package builds in `conda-explicit.txt` and lock | Downloaded during install | mixture of open-source licenses | Generate final notices from resolved environment |
| Noto CJK / Qt translation | installer assets | Bundled in installer | notices present in template | Preserve notices in rebuilt archives |

The current download lock contains 44 direct wheel entries; seven have an empty license field. Empty metadata is not treated as prohibition or permission. Before publication, resolve each against authoritative upstream/package license material and archive the evidence. The root MIT license never replaces these terms.

The repository MIT license and `CITATION.cff` currently name 李瑞熙. Because these files were added during release preparation rather than inherited from the teacher's frozen baseline, the teacher/actual rightsholder must confirm authorization and the copyright wording before public visibility.
