> Historical planning document from the initial implementation. For executed results and current status, see [the project README](../README.md), [methods](10_methods.md) and [HTML report](../index.html).

# Resource estimates

## Observed local resources
12 logical CPUs; 3.7 GiB total RAM, approximately 2.7 GiB available at inspection; 1 GiB swap. Project filesystem: approximately 941 GiB free of 1007 GiB. /tmp is a separate 1.9 GiB tmpfs and is unsuitable for fasterq-dump scratch. Free space can change; check before each large step. Use a configurable disk-backed scratch directory on the project filesystem or cluster scratch.

## Provisional budgets, not benchmark results
| Stage | CPUs | RAM | Disk / elapsed-time planning |
|---|---:|---:|---|
| Environment solve/install | 1–2 | 1–4 GiB | 5–15 GB per environment; solver may exceed local RAM |
| SRA download/conversion | 2 local / 4 HPC | 1–4 GiB | Reserve up to 20× archived SRA size plus retained outputs until actual run estimates refine this; network-dependent |
| QC | 2 local / 4 HPC | 1–4 GiB | Retain raw plus cleaned reads; minutes to hours by run size |
| 100,000-pair subsampling | 1–2 | <1 GiB with streaming implementation | For PE150: about 60 MB sequence + quality before headers/compression; seconds to minutes |
| Small synthetic Kraken2 database | 1–2 | target <1 GiB | Small test reference set; proves mechanics only |
| Broad Kraken2 screening | 4–8 | database-dependent, often tens to >100 GiB | HPC only unless a chosen database demonstrably fits; minutes to hours |
| Bracken | 1–2 | database-dependent | Requires matching k-mer/read-length distribution files |
| Bowtie2 mapping | 2 local / 4 HPC | index-dependent, ~1–8 GiB for small references | Index + sorted BAM + sort scratch; host competitive index may exceed local RAM |
| Coverage/aggregation | 1–2 | ~0.5–2 GiB if streamed | Whole-genome depth output can be large; gzip profiles or summarize incrementally |
| Optional viral assembly/protein search | 4–8 | 8–32 GiB or more | HPC only; multi-hour jobs possible; not installed or run by default |
| Tables/plots/report | 1–2 | 1–2 GiB | Usually <1 GB and minutes |

For each run let S be SRA bytes, F expanded paired FASTQ bytes, C retained compressed FASTQ, B alignments and D database storage. Budget at least S + F + conversion scratch + C + cleaned/subsampled outputs + B + D. A 20×S conversion allowance is provisional, not a guarantee for every archive. Query fasterq-dump size checks, available space and tool documentation before download. Do not use a universal fixed database size. Record the chosen release's compressed size, expansion and RAM expectations before approval.

Conservative local default: 2 threads and synthetic/100,000-pair tests. Cluster resource requests must come from editable YAML through qsub arguments; memory, queue and walltime depend on the selected run, database and site limits. No full broad database or full RNA assembly is currently authorized.
