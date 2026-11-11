# Third-party notices

PathPocket v1.0.7 uses third-party software and data. The root MIT license applies only to PathPocket-owned material and does not replace or relicense third-party components.

## Included in the installers

- **ED2Mol source**: the v1.0.6 distribution records frozen source identity `09f133da913179f82b285dbb046f1ecb81d1da37`. Its exact relationship to the public upstream repository and the provenance of each distributed file remain to be verified. The upstream project provides an MIT license text retained at `LICENSES/ED2Mol-MIT.txt`; that text alone does not establish the provenance of every file in the frozen subset. Model weights are not bundled or automatically downloaded; the user must supply a local archive matching the locked SHA256.
- **Noto Sans CJK**: `NotoSansCJK-Regular.ttc`, under SIL Open Font License 1.1. The retained text is at `LICENSES/Noto-CJK-OFL-1.1.txt`.
- **PDB demo coordinates**: demo inputs reference PDB entries 1AO6, 1N5U, 1E78 and 7KWZ. RCSB PDB identifies archive data as CC0 1.0; users should cite the PDB and the relevant structure publications.
- **Qt translation material**: the installer carries `qtbase_zh_CN.qm`. Applicable GPL/LGPL texts are retained under `LICENSES/Qt/`.

## Downloaded during first-run installation

The planned installer obtains exact hash-locked packages from upstream distribution services rather than bundling a preinstalled runtime. This includes conda-forge runtime packages, fpocket 4.2.3, PyTorch/CUDA userspace wheels and PySide6/Shiboken6 6.8.3. ED2Mol weights and smina are not downloaded automatically: users must obtain appropriately licensed copies and supply local files. The installer does not install or redistribute an NVIDIA display driver. Package-specific notices and license obligations must be checked for each actual component and delivery method before release.

- **fpocket 4.2.3** is obtained from conda-forge; upstream fpocket is MIT licensed. The retained upstream text is at `LICENSES/fpocket-MIT.txt`.
- **PySide6 / Qt / Shiboken6 6.8.3** are intended to be installed from locked community wheels. LGPL/GPL texts are retained under `LICENSES/Qt/`. Qt for Python also contains components under other licenses; see the [upstream 6.8 license list](https://doc.qt.io/qtforpython-6.8/licenses.html). Applicable component notices, source availability, and the actual ability to replace compatible libraries in the installed runtime remain to be checked before release.
- **NVIDIA/CUDA userspace packages** retain their package-specific terms. No single generic MIT or CUDA notice substitutes for those package-local terms.

The complete internal audit, wheel metadata and evidence are intentionally kept outside the public source repository and release assets. Nothing in the PathPocket license grants additional rights in these third-party components.

## Remaining permission questions

The available upstream material establishes the source and hashes of the ED2Mol v1.1 weight archive and locked `smina.static` asset, but does not expressly settle their specific license scope. Confirmation from the respective rightsholder is still required. User supply and hash verification are not evidence of authorization.
