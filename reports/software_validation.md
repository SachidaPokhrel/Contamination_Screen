# Software evidence

The transferred HPC inventory records installed SRA Toolkit3.2.1, FastQC0.12.1,
fastp0.24.3, SeqKit2.14.0, Kraken2 2.1.6, Bracken3.0.1, Bowtie2 2.5.5,
SAMtools1.21, minimap2 2.31, BLAST2.16.0+ and R4.4.3. SPAdes4.2.0 appears in
actual DNA/RNA assembly logs. BlobToolKit commands and R figure outputs completed
successfully on HPC; exact package records are retained in environments/.

See [the original environment inventory](../provenance/hpc_validation_20261017/environment.tsv)
and [stage history](../provenance/run_history.tsv). Current curation ran only
Python/Bash offline tests, HTML generation and artifact checks; bioinformatics
software was not installed or rerun on this local computer. DIAMOND/CheckV execution is not established. The additional FCS case is evidenced by its supplied reports and original log, as described below.


## Added public-genome FCS-GX case (2026-10-20)

The separate *Globisporangium irregulare* strain 13-30 assembly GCA_051997085.1
(PRJNA816194; SAMN26664723) was selected because **the user reports NCBI flagged
it as contaminated**; exact flag wording was not independently retrieved.
Supplied completed FCS-GX outputs recommend excluding eight fungal-labelled
contigs: 12,358 bp, 0.028973% of assembly bases. This is independent of the
original two SRA readsets; no SRA run or raw-read metrics were verified for this
additional case. Student bins/sources remain unassigned. See the
[FCS case report](../reports/fcs_analysis.md) and
[portable Linux instructions](../docs/15_fcs_linux.md).
