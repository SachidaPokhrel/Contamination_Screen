> Historical planning document from the initial implementation. For executed results and current status, see [the project README](../README.md), [methods](10_methods.md) and [HTML report](../index.html).

# Pipeline design

The implementations below exist. Biological external-tool stages remain unexecuted locally; see validation reports for exact executed checks. Each entry will become an independently runnable script supporting --help, shared validated configuration, live stdout/stderr logs, software versions, timestamps and explicit completion verification.

| Stage/script | Inputs | Core command/tool | Outputs | Dependencies |
|---|---|---|---|---|
| 00_check_environment.sh | configuration and host system | command -v; Python platform/resource checks | environment report | Bash, Python |
| 01_download_data.sh | verified config/datasets.tsv | prefetch; vdb-validate; fasterq-dump --split-files; pigz | separate DNA/RNA FASTQ, checksums, manifest | SRA Toolkit, compressor, disk scratch |
| 02_read_qc.sh | complete paired raw FASTQ | fastqc; fastp --in1/--in2; post-QC | cleaned pairs, HTML/JSON/statistics | FastQC, fastp |
| 03_subsample.sh | cleaned paired FASTQ | streaming paired reservoir sampling with fixed seed | 100,000 pairs or all available if fewer, recorded denominator | Python; seqkit for inspection |
| 04_kraken2_screen.sh | selected reads, validated DB | kraken2 --paired --report | assignments, report, DB provenance | Kraken2 |
| 05_bracken_abundance.sh | Kraken report, compatible DB model | bracken -r configured_length | abundance TSV, assumptions | Bracken |
| 06_select_candidates.py | report, expected taxids/lineage metadata | rank, flag and label taxa | ranked TSV, manual selection template | Python/pandas |
| 07_download_references.sh | manually selected versioned accessions | NCBI retrieval, FASTA validation, checksums | reference FASTA, metadata, accession/contig map | HTTPS client, Python, Bowtie2 |
| 08_mapping.sh | read pairs, references | bowtie2; samtools sort/index/flagstat | candidate-only and optional competitive BAM, metrics | Bowtie2, SAMtools |
| 09_coverage.sh | filtered BAM, reference lengths, denominator | samtools depth -aa; streaming aggregation | per-reference coverage metrics and profiles | SAMtools, Python |
| 10_rna_virus_screen.sh | RNA candidates, viral references | reference mapping/coverage; optional megahit + diamond blastx | evidence-linked viral table and optional contigs | mapping stack; optional viral environment |
| 11_detection_table.py | screening and mapping evidence | keyed validated joins | detections.tsv/csv with blank interpretation fields | Python/pandas |
| 12_visualization.R | evidence tables and profiles | ggplot2 | PNG/PDF plots | R plotting environment |
| 13_generate_report.py | detections table | deterministic Markdown template | one-page editable report | Python |
| run_pipeline.sh | stage range/config | dependency-aware stage calls | execution manifest and stage logs | relevant stage dependencies |

## Evidence definitions
Use the same readset for candidate comparison and its denominator; retain full/subsample provenance. Read fraction = 100 × primary mapped reads passing configured MAPQ/flag filters / all input sequencing reads in that exact paired readset. Record reads and distinct paired fragments separately. Do not equate paired reads with fragments or Kraken classified percentages with mapping read fractions. Exclude unmapped, secondary and supplementary alignments; make duplicate policy explicit. Count fragments by read identity under a documented either-mate or both-mates policy.

Mean depth = summed retained aligned base depth / full reference length. Breadth at threshold t = 100 × positions with depth ≥t / full reference length. Sum numerators and lengths across contigs before division, including entirely uncovered contigs. Document overlapping-mate treatment and how deletion/refskip positions are counted. Provide contig-level profiles and aggregate metrics. MAPQ thresholds and aligner multimapping behavior are evidence caveats, not proof of unique biological origin.

Candidate-only alignments establish compatibility; competitive alignment against host plus candidates helps expose shared/repetitive support. RNA spliced host reads require caution: Bowtie2 is appropriate for contiguous viral genomes but is not a splice-aware host transcriptome aligner. Prefer an explicit host transcriptome for RNA competition or document genomic competition limitations. Optional host subtraction must not silently discard reads needed to test integrated or shared regions.

## Restart and portability contracts
Resolve relative configuration paths against the project root, never the caller's current directory. Allow absolute external paths and environment overrides. No developer-machine absolute path enters generated scripts. Use temporary files and atomic rename, per-stage input/config/version signatures and output checksums; a sentinel alone is insufficient verification. Changed inputs require explicit rebuild or a clear stale-output error. Downloads support prefetch resumption and validate both FASTQ structure and mate identifiers before completion.

DB preparation is separate and opt-in: validate hash.k2d, opts.k2d and taxo.k2d, record release/taxonomy/coverage when known, and check compatible Bracken distributions. A tiny synthetic DB validates execution and cannot represent comprehensive oomycete/viral screening. Unknown DB coverage stays explicitly unknown.

## PBS contract
qsub resource flags are rendered from hpc_resources.yaml by submit_pipeline.sh; PBS does not expand shell variables in #PBS directives. Individually submitted wrappers use conservative literal defaults, with qsub -q/-l overrides documented. Resolve project root from an explicit exported project path or PBS_O_WORKDIR by walking to project markers; fail clearly if neither resolves. Activate recreated YAML environments. Use afterok dependencies and stop on submission failure. Redirect scheduler output to logs/pbs through submission arguments; individual jobs move/redirect streams after root resolution, acknowledging site-specific initial spool output. Download on transfer/login nodes only where site policy allows; never assume compute-node internet. Manual candidate selection creates a deliberate boundary between screening jobs and reference/mapping jobs.
