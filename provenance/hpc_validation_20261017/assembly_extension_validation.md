# Assembly extension validation

Executed locally on 2026-10-18.

| Check | Result |
|---|---|
| GC denominator, all-N contig, multi-contig records, zero depth and taxon labels | PASS |
| CLI help and missing-assembly failure | PASS |
| Mock PBS afterok dependencies and optional FCS submission arguments | PASS |
| Bash/PBS syntax (8 new shell/PBS files) | PASS |
| Python compilation | PASS |

Not executed: BlobToolKit installation/import, R rendering, real minimap2/SAMtools
mapping, assembly Kraken2 classification, FCS-GX screening, live PBS submission.
Mock scheduler tests verify command construction only. HPC execution remains pending.
The FCS runner interface and BlobToolKit text-import syntax were checked against
upstream source. FCS database, container and module paths require site inspection.
