# Distribution source identity

PathPocket v1.0.7 is a GUI maintenance candidate derived from the published v1.0.6 source commit `b91023719d18e4889f8c6581c3ec7399674555b3`. The scientific backend retains its separate version, 0.3.0. The existing fpocket integration is unchanged and FLAME is not included.

The historically recorded ED2Mol engine identifier is `09f133da913179f82b285dbb046f1ecb81d1da37`. Its exact relationship to the public upstream repository and the provenance of the frozen files remain under review. The source repository does not include model weights or a preinstalled runtime; see `THIRD_PARTY_NOTICES.md` for outstanding asset permissions.

The repository contains the scientific backend under `src/`, the interface under `gui/`, tests under `tests/`, and installer source under `distribution/`. A source checkout is not a portable installer. The installer candidate and its assets require separate license, content and installation review before release.
