# RNA extension validation

Executed locally 2026-10-19.

| Check | Status |
|---|---|
| Mock assembler: RNA mode, paired arguments, unknown strandedness | PASS |
| Manifest contents and verified completed-stage skip | PASS |
| Missing read input stops before assembler | PASS |
| Interrupted assembly: explicit continuation, changed-input rejection | PASS |
| Mock PBS assembly/mapping/taxonomy/BlobToolKit afterok dependencies | PASS |
| Python compilation, CLI help, new Bash/PBS syntax | PASS |

The four unit tests exercise control flow using a mocked assembler and scheduler;
they do NOT validate biological assembly, mapping or classification. Real rnaSPAdes
installation/execution, R rendering and PBS submission remain pending on HPC.
Existing BlobToolKit environment and DNA tools are reused only after HPC verification.
