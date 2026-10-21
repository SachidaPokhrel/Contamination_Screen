# Delivery status after HPC analysis and repository curation

Current results are documented in ../index.html and ../README.md. The read-based
analyses, pluspf/Bracken comparison, published DNA assembly, de novo DNA assembly
and RNA transcriptome BlobToolKit branches have recorded successful HPC runs.
No completed FCS-GX output was supplied for the original readset assembly branches; the additional public-genome FCS case is documented below. No viral validation output was supplied. Raw reads and large
regenerable intermediates are intentionally not included. Final gzip assemblies,
measurement tables, plots, BlobDirs, logs and environments are retained. Scientific
significance/source fields remain student-editable. See repository_validation.md
for checks actually performed during this curation, and provenance/ for originals.


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
