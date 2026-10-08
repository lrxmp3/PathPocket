# Reproduce paper source data

Download/unzip the separately staged paper data archive. Run `python scripts/reproduce_paper/materialize.py <data-directory> <new-workspace>` to reconstruct original workspace-relative paths, resolving deduplication aliases and script `<WORKSPACE>` roots. It verifies each public hash before writing. This command restores saved evidence; it does not start an engine, simulation, new analysis or renderer.

The `make_fig3_data.py`, `make_fig4_data.py`, `make_fig5_data.py`, `make_s1.py` … `make_s4.py` commands restore the relevant evidence group. Figure 3 also uses group 02_7KWZ; figure assembly files are group 08_FIGURE_SOURCE_DATA. Use the full materializer for dependencies spanning groups.

Existing analysis entry points, preserved in the data archive:
- `50_MANUSCRIPT_APPLICATION/16_METHOD_STRENGTHENING/scripts/correspondence_analysis.py`: sensitivity and ablation.
- `.../scripts/volume_audit.py`: historical fpocket repeatability audit. Re-executing this would be new stochastic computation; the saved audit tables reproduce the displayed plot without rerunning fpocket.
- `.../scripts/summarize_new_results.py`: frozen-budget summaries and identity nesting.
- `.../scripts/build_supplementary_figures.py`: SI plots from saved tables.
- `50_MANUSCRIPT_APPLICATION/12_FIGURE_REVISION_V2/editorial_v4_build` and `portrait_45_v4_build`: figure scenes and assembly.
- `50_MANUSCRIPT_APPLICATION/18_MANUSCRIPT_V0_3/build/build_figure5.py` and saved `figure_5.json`: latest matched-budget update.

Historical scripts are provided for inspection and reuse, not silently invoked by these wrappers. Review paths, optional VMD/font requirements and helper imports before executing them in an isolated workspace. Certain authoring helpers belong to the original rendering environment and are not redistributed; saved vector/native scene artifacts remain available. A universal one-command pixel-identical renderer is not claimed. Scientific values and source selections are recorded in panel CSVs and maps. Do not run `launch_challenge.sh` merely to reproduce a plot.
