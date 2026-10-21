# FCS-GX: independent public-genome case

The additional genome is **Globisporangium irregulare strain 13-30**, assembly
**GCA_051997085.1**, BioProject **PRJNA816194**, BioSample **SAMN26664723**,
WGS master **JALBZS000000000**, taxid 36331. The assembly/sample linkage is
listed in the [NCBI BioProject assembly table](https://www.ncbi.nlm.nih.gov/bioproject/816194).
It is distinct from the original DNA SRR15309490 and RNA SRR16206986 datasets.
No SRA run for this additional genome was verified; this is not evidence that
associated reads do not exist. No raw reads from this case were analysed here.

## Why this genome was selected

**The user reports that NCBI flagged this assembly as contaminated.** The exact
current NCBI flag wording was not independently retrieved. The flag is recorded
as user-reported selection history in metadata/fcs_genome.json, separately from
the supplied FCS output. This was a known, previously flagged assembly case;
it is not a blind discovery or a detection-limit experiment.

## What ran and what was found

The supplied HPC action report records FCS-GX v0.5.0, database build 2023-01-24,
and a run dated October 14, 2026 (timezone unspecified). The tool output records
about 29,799 seconds (8.28 hours) processing. Job 102266 requested 40 GB and two
CPUs; these are requested resources, not measured peak use or a universal minimum.

| Measurement | Input | Retained | Excluded |
|---|---:|---:|---:|
| Sequences | 5,451 | 5,443 | 8 |
| Bases | 42,653,821 | 42,641,463 | 12,358 |

All eight actions are full-contig **EXCLUDE**, division `fung:ascomycetes`.
Six contigs (10,225 bp) have top label *Cladosporium colombiae*; two (2,133 bp)
have top label *Melanodothis* sp. VS III C KN 2. Together they represent
**0.0289728% of input assembly bases**. The exact contigs and FCS alignment
coverage values are in [fcs_actions.tsv](../tables/fcs_actions.tsv).

The original, retained and excluded FASTAs were audited locally: identifier
sets form an exact partition, and sequences match ignoring letter case.
Cleaning uppercased sequence; original lowercase soft masking was not preserved.
No new FCS container screening was performed during repository integration.

## What this means—and what remains undecided

This supplies assembly-level evidence for FCS-classified non-target fungal
sequence and documents the tool's exclusion recommendation. Top species names
are provisional similarity labels. The result does not establish viable fungi,
a real associate, reagent contamination, integration, or a particular transfer
mechanism. An NCBI flag does not independently prove any of those sources either.
Nor does the retained file establish that all remaining sequence is contaminant-free.

**Read fraction, read depth and read-mapping breadth are unavailable for this
assembly-only case.** FCS `agg_cont_cov` is foreign-division alignment coverage,
not sequencing-read breadth. Assembly-base percentage must not be inserted into
the original read-fraction column. A separate [FCS detection table](../tables/fcs_detections.tsv)
leaves read metrics, significance bins and likely sources blank for student review.

The original Pseudomonas read-screening case remains a separate specificity
exercise; none of its read counts or conclusions are replaced by this genome.
The three embedded BlobToolKit figures describe the original assembly branches,
not this additional FCS genome.

## Evidence

- Original action/taxonomy reports and FASTAs: [fcs/](../fcs/README.md).
- Original HPC stdout: [screen_class.o102266](../fcs/screen_class.o102266).
- Machine-readable audit: [fcs_results.json](fcs_results.json).
- Dataset relationships and unresolved SRA linkage: [analysis_datasets.tsv](../metadata/analysis_datasets.tsv).
- Portable rerun instructions: [15_fcs_linux.md](../docs/15_fcs_linux.md).

Student final decision: **bin ______; likely source ______**. Explain why the
observed contig evidence supports that choice over alternatives, and identify
which source claims would require raw reads, controls or additional validation.
