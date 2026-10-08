# PathPocket v1.0.6

This release preserves the PathPocket v1.0.6 interface, workflow, report templates, and scientific settings used for the paper baseline.

## Maintenance fixes included

- The trusted built-in NO_TARGETS engineering example now produces an empty selected-target set at the target-selection boundary, skips ED2Mol, generates zero molecules, and completes through the normal zero-target result path.
- The engineering fixture remains isolated from ordinary HSA and 7KWZ projects and records its identity and origin in run evidence.
- Paths containing spaces are handled by the existing packaged path-transport layer.
- Existing completed results with molecule records automatically render their saved two-dimensional molecular structures; empty NO_TARGETS results do not start molecule drawing.

## Scientific boundary

No fpocket or ED2Mol algorithms, model weights, target-selection thresholds, generation parameters, random seeds, molecular descriptors, quality-control rules, ranking rules, or statistical definitions were changed. No v1.0.7 interface redesign or FLAME functionality is included.

NO_TARGETS is an engineering test of zero selected targets. It is not evidence that the input protein has no pockets.

## Distribution status

This repository is the source distribution. Model weights, scientific runtime binaries, fpocket binaries, CUDA/PyTorch binaries, and molecular viewers are not bundled. See `third_party/README.md` and the installation guides.

## License and citation

PathPocket-owned source code is released under the MIT License. This license does not alter the separate terms for third-party code, model weights, runtime binaries, or external structure/data assets. Please cite the PathPocket software and, after publication, the accompanying paper; the paper citation and software DOI will be added when available.
