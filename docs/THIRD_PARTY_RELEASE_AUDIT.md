# Third-party delivery summary

This is the publishable delivery summary, not the internal license audit. Complete package metadata and evidence remain outside the source repository and release assets.

| Component | Actual delivery | Retained notice | Status |
| --- | --- | --- | --- |
| ED2Mol source | historical frozen subset under review | `LICENSES/ED2Mol-MIT.txt` | exact upstream relationship and file provenance pending |
| ED2Mol v1.1 weights | automatic download; SHA256 locked | upstream project notice | external-asset scope awaiting rightsholder confirmation |
| `smina.static` | automatic download; SHA256 locked | upstream provenance recorded internally | binary-asset scope awaiting rightsholder confirmation |
| Noto Sans CJK | font included | `LICENSES/Noto-CJK-OFL-1.1.txt` | evidence retained |
| Qt translation | translation file included | `LICENSES/Qt/` | evidence retained |
| fpocket 4.2.3 | conda-forge download at first run | `LICENSES/fpocket-MIT.txt` plus package-local metadata | evidence retained |
| PySide6/Qt/Shiboken 6.8.3 | locked upstream wheels planned for first-run download | `LICENSES/Qt/`; component-specific notices under review | source, applicable notices and library replacement in the actual installation remain to be verified |
| CUDA/PyTorch userspace packages | locked upstream wheels downloaded at first run | package-local terms | no NVIDIA display driver bundled |

The root MIT license applies only to PathPocket-owned source and documentation. For user-facing attribution and the exact unresolved external-asset questions, see `THIRD_PARTY_NOTICES.md`.
