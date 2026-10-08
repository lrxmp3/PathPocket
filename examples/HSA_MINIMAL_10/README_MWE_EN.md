# HSA minimal example

HSA 1N5U chain A; frozen family RF_0011; one target RF_0011_state_B; 10 requested molecules, seed 42, iteration 2.

Prepare a new workspace with the repository scripts/run_mwe.py, or have the maintainer import the example into an installed portable GUI. Then open the project: Validate → Backend doctor → Run. A working GPU scientific runtime is required. This packaging round validates inputs/configuration/paths without new generation. expected/contract.json specifies structural acceptance, not identical molecular bytes.


Preparation command from the source repository: `python scripts/run_mwe.py --workspace <new-workspace> --runtime <installed-PathPocket_Linux-root>`. It creates a new `20_PROJECTS/HSA_MINIMAL_10` project and resolves local receptor paths. On Linux/WSL, add `--run` only when you intend to run the installed doctor and generate molecules; this was not executed during packaging.


Preparation command from the source repository: `python scripts/run_mwe.py --workspace <new-workspace> --runtime <installed-PathPocket_Linux-root>`. It creates a new `20_PROJECTS/HSA_MINIMAL_10` project and resolves local receptor paths. On Linux/WSL, add `--run` only when you intend to run the installed doctor and generate molecules; this was not executed during packaging.
