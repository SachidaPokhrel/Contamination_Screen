# De novo DNA extension validation

Local checks executed 2026-10-19.

| Check | Result |
|---|---|
| Mock SPAdes invocation: DNA mode, both mates, no reference-guided flags | PASS |
| Contig summary, N50, and verified restart skip | PASS |
| Missing input failure and changed-input resume refusal | PASS |
| Interrupted SPAdes checkpoint continuation | PASS |
| Mock PBS afterok dependency graph | PASS |
| Mock FCS receives new contigs, never published assembly from software settings | PASS |
| Python compilation, CLI help and nine Bash/PBS files syntax | PASS |

Five unit tests use mocked external tools/scheduler. No real DNA assembly,
alignment, Kraken classification, BlobToolKit import, R plot, FCS screening or
live scheduler submission was performed locally for this branch. Prior user-run
published-assembly results do not validate this new assembly branch.
