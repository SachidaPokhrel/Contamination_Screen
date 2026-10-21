# Implementation decisions

- 2026-10-17: Begin with an approval-gated design, as requested; no installations or sequencing downloads during Phase 1.
- Use Linux Bash inside WSL2, with portable Python configuration helpers and R plots.
- Default local jobs to two threads because RAM, rather than CPU availability, is the limiting resource.
- Avoid /tmp for SRA conversion because it is a small RAM-backed filesystem.
- Keep environment definitions portable; recreate environments on HPC rather than transfer binaries.
- Use synthetic fixtures before biological data, and keep synthetic outputs visibly separate from scientific detections.
- Treat Kraken2 detections as candidate hypotheses requiring mapping/coverage validation.
- Preserve student-authored significance/source/interpretation fields as blanks.
- Require manual candidate selection before mapping; PBS submission will respect that checkpoint.
- No run accessions are guessed from BioProject or assembly records. Dataset selection remains pending.
- Record shell DNS failure separately from browsing-service availability; do not claim automated downloads work yet.

- User approved the plan on 2026-10-17; implementation proceeded without additional routine approval requests.
- Selected provisional directly verified low-size runs SRR15309490 and SRR16206986. Preferred G. irregulare and virus-associated project leads remain recorded with unresolved run metadata rather than guessed accessions.
- Shipped JSON-compatible YAML permits bootstrap using Python standard library; ordinary YAML is supported when PyYAML is installed.
- Numbered scripts delegate to a tested shared Python implementation so validation, paths and logging are consistent.
- Results have sample subdirectories and per-mode joint-candidate/competitive outputs to prevent cross-sample overwrites.
- External read-only Kraken databases are never modified for provenance; checksums/manifests live in the project databases directory.
- Stage signatures and output manifests store project-relative paths; a relocation test passed after correcting default-root resolution.
- Candidate-only mapping includes all reviewed candidates together, which reduces repeated attribution between individually mapped candidate references.
- RNA competition can use host transcriptomes; default genomic reference leads produce explicit non-splice-aware caveats.
- Full-data download, reference download, database download, Bracken and expensive virus discovery remain off by default.
- Real tool installation is blocked by absent Conda managers and shell DNS failure; fixture tests do not stand in for external-tool validation.

- Subsequent user approval authorizes sequencing retrieval for SRR15309490 and SRR16206986 (~1.56 GB combined). Enabled allow_data_download; reference/database permissions stay false. Approval persists across deployment and retries.
