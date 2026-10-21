# Curation summary

- Source: transferred Contamination_Scan HPC results copy, approximately5.8GiB.
-441 files totalling6,092,222,610 bytes were moved to an external recovery copy
  rather than permanently deleted. Original relative paths and SHA256 values are
  listed in ../metadata/repository_cleanup.tsv.
- Final DNA contigs and RNA transcripts were retained losslessly as gzip, with
  original uncompressed and compressed checksums and a restoration script.
- Primary detection TSV/CSV measurements and user-editable interpretation fields
  were preserved unchanged. New supplementary summaries are explicitly named.
- Duplicate installers, accidental zero-byte shell artifacts, obsolete generated
  demo copies, bytecode, corrected reads, indexes, BAMs, full depth and graph/checkpoint
  intermediates were removed from the publication directory.
- Completed published-DNA, de novo-DNA and RNA BlobToolKit outputs are retained.
  No completed FCS/viral discovery is invented.
- Root HTML embeds all seven selected figures. Directory descriptions, annotated
  core functions, repository/restoration guides, offline tests and CI are included.
- Raw readsets were not supplied and are not bundled. No compiled environment or
  external taxonomy database is included. No commit/push was performed.

Recovery location in this workspace: ../Contamination_Scan_recovery_20261020/,
relative to the repository root's parent. It is intentionally outside this Git
repository; do not include it in a GitHub upload. Current validation is in
repository_validation.md and verification/tests.md.
