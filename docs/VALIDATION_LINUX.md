# Direct Linux candidate validation

| Check | Current candidate status | Evidence / reason |
| --- | --- | --- |
| Source and installer scripts | Static review in progress | `distribution/linux/`; shared core is the release branch |
| Unit tests | Partial PASS | Focused installer/path/zero-contract suite; any unavailable dependency is recorded separately |
| Final archive extraction/checksum | Pending rebuild | Final candidate archive not yet generated |
| Fresh direct installation | NOT TESTED | Must use the rebuilt archive in an independent path |
| GUI v1.0.6 / HSA / 7KWZ / NO_TARGETS | NOT TESTED for candidate | Historical runs belong to older packages |
| Report, folder, SDF, complex export | NOT TESTED for candidate | Requires direct desktop acceptance |

Historical Ubuntu 22.04.5, RTX 3080 Ti, driver 580.65.06 evidence proves an older package could install and run HSA/7KWZ, but that package selected three targets and generated 60 molecules in its NO_TARGETS test. It therefore cannot be marked PASS for the repaired candidate. Ubuntu 24.04 direct installation also remains untested.
