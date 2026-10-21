# Reconstructed collaboration summary (not a verbatim transcript)

This summary is based on the available conversation and retained HPC evidence.
A verified complete chat export was not available; no transcript is fabricated.

- Initial planning covered portable environments, paired SRA retrieval, QC,
  subsampling, read screening, reviewed reference mapping and objective coverage.
- HPC installation exposed tool-specific version flags and permissions; those
  issues were corrected before successful tool checks and downloads.
- Original Kraken screening used100,000 pairs per assay, followed by representative
  reference mapping and expanded RNA validation.
- Specificity review found conserved rRNA/tRNA support and alternate oomycete
  matches for the Pseudomonas pilot. Student significance/source judgments were
  deliberately left open. The Miltoncostaea interval BLAST was skipped.
- Matching Bracken files were discovered under a different ~1TB nt database;
  those were not mixed with original reports. A separate pluspf comparison ran.
- Published DNA assembly screening and BlobToolKit completed; then independent
  de novo DNA and RNA assemblies and BlobToolKit branches completed on HPC.
- FCS-GX submission encountered a site memory-parsing hook; no completed report
  appears in the supplied results. RNA assembly did not include protein-based
  virus discovery.
- On2026-10-20 the transferred results were curated locally, with removed files
  recovered outside the repository, annotated code, directory guides and an
  offline HTML evidence report. Original measurements were preserved.

For exact commands, timestamps, errors and output paths use logs/. For an extracted
chronology use provenance/run_history.tsv; these are execution records, not chat.


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
