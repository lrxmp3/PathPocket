# PathPocket v1.0.7 — GUI maintenance candidate

This development candidate is based on the published v1.0.6 source. The run page can display per-target ED2Mol batch progress read from the generator log. Batch progress is not the number of molecules produced; written molecule counts remain separate. Chinese and English labels are available.

Scientific backend version 0.3.0 and the existing fpocket implementation are unchanged. FLAME is not included. Installation and distribution assets remain under preparation; this document does not announce a released package.

The candidate installer does not bundle or automatically download the ED2Mol weights or smina binary. New generation requires user-supplied local files matching the locked hashes; the scope of authorization for those assets still needs confirmation. See the installation guide and third-party notices.
