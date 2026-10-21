# Methods used in the completed analysis

## Samples and preprocessing

Independent paired Illumina datasets SRR15309490 (Globisporangium okanoganense
CBS315.81; WGS) and SRR16206986 (Phytophthora hibernalis mycelium; RNA-seq) were
retrieved with SRA Toolkit prefetch, checked with vdb-validate, converted using
fasterq-dump and compressed. FastQC and fastp produced raw/cleaned QC reports.
Validated retained pairs were 5,685,476 DNA and 5,941,455 RNA. Raw files are not
included in this repository. Original parameters, commands, timestamps and software
versions are retained in logs and package metadata.

## Read screening and reference validation

Paired fragments were subsampled reproducibly to 100,000 per assay using seed1729.
Kraken2 with confidence0.1 classified paired reads against the cluster's original
kraken2_full index. Candidate rankings retained low-support and ambiguous labels.
Manual reference selection led to candidate-only and host-competitive Bowtie2
alignments, sorted/indexed with SAMtools. RNA host competition used a genome,
not a transcriptome, limiting treatment of splice-spanning reads. The original
DNA host assembly GCA_023334035.1 matches BioSample SAMN13878593; the RNA host
assembly GCA_024679025.1 is same-species but not verified as the same RNA isolate.

Coverage filters were MAPQ>=20, exclusion of MAPQ255 and SAM flags3844; base-quality
threshold0. Only pre-existing duplicate flags were excluded; no duplicate marking
was performed. Primary aligned reads were counted separately from distinct paired
fragment names. Read fraction = supporting reads /200,000 x100; fragment fraction
= supporting fragment names /100,000 x100. Either mate can support a reference,
so discordant reference fragment counts must not be summed as disjoint groups.
SAMtools depth used all reference positions, removed overlapping mate bases and
excluded deletion/refskip bases. Mean depth sums depth over full reference length;
breadths report fractions of all reference bases at >=1x, >=5x and >=10x, correctly
aggregated over contigs. The RNA expanded reference round is retained separately;
final detections combine original DNA and expanded RNA results.

## Specificity audit

Pseudomonas reference alignments were intersected with annotated CP087163.1 rRNA
intervals using CIGAR M/= /X reference-aligned bases (deletions/skips excluded).
Two non-rRNA RNA alignments were annotated from chromosome windows, finding tRNA-Gln
and sucD. Selected read pairs were compared to NCBI nt with remote blastn; exact
queries and outputs are retained. Representative searches do not assign every
supporting read's origin. Miltoncostaea alignments were inspected at a single130bp
locus; a subsequent optional interval BLAST was skipped.

## Separate abundance comparison

The same paired subsamples were classified against pluspf, then Bracken estimated
species-level abundance with matching 150bp DNA and100bp RNA database distributions.
The latter approximates predominantly90bp RNA reads. The pipeline used the default
Bracken support threshold; original command/version logs are retained. Bracken's
fraction_total_reads is normalized within its modeled species-level allocation,
not all input pairs. The supplementary comparison explicitly reports estimated
fragments/100,000 separately. RNA abundance also reflects expression and library
preparation. These estimates do not replace mapping fractions or confirm species.

## Assembly and BlobToolKit

The published DNA reference was analysed separately from assemblies generated from
the actual reads. SPAdes4.2.0 in standard DNA mode assembled all cleaned DNA pairs
without reference guidance; rnaSPAdes mode assembled all cleaned RNA pairs, leaving
strand-specificity unknown and retaining transcripts.fasta. Full cleaned mates were
mapped back with minimap2 -ax sr, sorted and filtered at MAPQ20 and flags3844.
SAMtools coverage provided per-contig mean depth including uncovered positions.
Assembly coverage retains overlapping mate contributions and is not numerically
identical to the earlier candidate depth definition. RNA isoforms and expression
complicate interpretation; it is not TPM or cell abundance.

Kraken2 classified assembly contigs against pluspf. BlobToolKit imported native
sequence statistics and custom retained-depth/Kraken-label fields. Static PNG/PDF
GC-depth blobplots were rendered by R ggplot2 from the same contig table: x=GC
fraction among A/C/G/T, y=mean retained depth+0.001 on a log scale, point area=length,
colour=provisional Kraken label. Native BlobDirs are preserved. Whole-contig labels
can miss internal chimeras and require independent validation.

## Scope

For the original readset assembly branches, no completed FCS-GX, viral protein-similarity validation, CheckV, or spike-in test
is reported. All significance bins and likely sources remain user decisions.
Current repository-only validation is distinguished from historical HPC execution.
Tool sources: [SPAdes](https://ablab.github.io/spades/),
[Kraken2](https://github.com/DerrickWood/kraken2),
[Bracken](https://github.com/jenniferlu717/Bracken),
[Bowtie2](https://bowtie-bio.sourceforge.net/bowtie2/manual.shtml),
[SAMtools](https://www.htslib.org/doc/),
[BlobToolKit](https://github.com/genomehubs/blobtoolkit).


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
