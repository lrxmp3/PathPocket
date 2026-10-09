# Source alignment record — 2026-10-09

## Candidate architecture

The direct-Linux and Windows 11/WSL2 installers use the same Linux GUI/backend core. Windows-only files provision Ubuntu 24.04, translate paths, create a Windows shortcut and invoke WSLg. They do not provide a native Windows scientific engine.

## Windows R1 trace

- External source identity: `d616f58b4b7c698e03b627a67e7923ef0c93ef2b`.
- The Git object is not present in this local repository. The supplied R1 delivery contains its baseline-to-head diff, source identity, tests and final archive hashes.
- The R1 nested Linux runtime GUI/backend files matched private branch commit `45c58fb97f807e2b2b5279830257e468f858979d` by file hash before integration.
- R1's functional change (raw native-output capture; BOM/encoding detection; NUL removal; correct WSL2 D_READY classification) was integrated manually from the preserved diff. This is not represented as a cherry-pick. The eventual integration commit is the local trace target for `d616f58`.

## Shared-core follow-up

R1 evidence showed that `explorer.exe` failed when asked to open report files. The shared WSL path adapter now uses `rundll32.exe url.dll,FileProtocolHandler` for files and retains `explorer.exe` for directories. This does not alter report generation, SDF contents, scientific algorithms or GUI layout. It is unit-tested but needs rebuilt-package Windows validation.

## Linux provenance

The preserved Linux HF5 package has SHA256 `f38eaa9dddaeb8aa28b7e78f8bd88a33a3734fbb7b470cdd3644f5cc0ebe84db`. It predates current shared-core repairs and is a template/provenance input, not the final candidate. A historical external Linux evidence archive has SHA256 `82eab2ade1ac648c7ded60e479bbbb3db4764d4331bcb210ce7ca4766e928e6a`; its NO_TARGETS run failed and cannot validate the candidate.

Both final installers must be rebuilt from the same integration commit and recorded by final filename, SHA256, build command and source SHA.
