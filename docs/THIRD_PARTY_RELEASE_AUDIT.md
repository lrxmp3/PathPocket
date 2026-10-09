# Third-party delivery summary

This is the publishable delivery summary, not the internal license audit. Complete package metadata and evidence remain outside the source repository and release assets.

| Component | Actual delivery | Retained notice | Status |
| --- | --- | --- | --- |
| ED2Mol source | frozen source subset included | `LICENSES/ED2Mol-MIT.txt` | evidence retained |
| ED2Mol v1.1 weights | downloaded from official release; SHA256 locked | upstream project notice | external-asset scope awaiting rightsholder confirmation |
| `smina.static` | downloaded from locked upstream location | upstream provenance recorded internally | binary-asset scope awaiting rightsholder confirmation |
| Noto Sans CJK | font included | `LICENSES/Noto-CJK-OFL-1.1.txt` | evidence retained |
| Qt translation | translation file included | `LICENSES/Qt/` | evidence retained |
| fpocket 4.2.3 | conda-forge download at first run | `LICENSES/fpocket-MIT.txt` plus package-local metadata | evidence retained |
| PySide6/Qt/Shiboken 6.8.3 | locked upstream wheels downloaded at first run | `LICENSES/Qt/` plus wheel-local notices | delivery measures documented |
| CUDA/PyTorch userspace packages | locked upstream wheels downloaded at first run | package-local terms | no NVIDIA display driver bundled |

The root MIT license applies only to PathPocket-owned source and documentation. For user-facing attribution and the exact unresolved external-asset questions, see `THIRD_PARTY_NOTICES.md`.
