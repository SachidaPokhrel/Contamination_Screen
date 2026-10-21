# Repository curation, recovery and reproduction

## What the repository contains

This is the curated HPC results repository, not the earlier planning-only local
project. Source layout and sample IDs are preserved. `results/` contains the original
screening and all assembly branches; `results_round2/` records expanded RNA mapping;
`results_pluspf/` records separate Kraken2/Bracken estimates. `results_final/` contains
portable relative links selecting original DNA plus round-two RNA results.
Run `python3 scripts/prepare_final_view.py` if a transfer tool loses those links.

The primary detections.tsv/csv have not been altered by curation. New summary TSVs
are derived by scripts/build_report.py. Blank significance/source columns are
intentional student-editable fields, not missing classifier results.

## What was removed from the publication directory

A recovery copy outside the Git repository preserves removed files at original
relative paths, with SHA256/size/reason in metadata/repository_cleanup.tsv.
It contains accidental zero-byte paste artifacts, delivery installers, duplicate
backups/demo output, Python caches, corrected read FASTQs, BAM/index files, full
per-position depth, downloaded reference FASTA, and unused SPAdes graph/checkpoint
products. None are needed to read the final results. Do not publish the recovery
copy as part of this repository. Original HPC stdout/stderr logs remain unchanged.

Final de novo DNA and RNA FASTAs are retained as deterministic gzip files with
compressed and uncompressed SHA256 in metadata/retained_assemblies.json. Restore:

```
python3 scripts/restore_artifacts.py
```

No raw SRA or cleaned FASTQs were supplied. Reproduction of compute stages therefore
requires downloading/QC again or restoring those readsets from your HPC storage.
Removing assembler checkpoints means `--resume` cannot continue the historical
assembly from the curated copy; completed FASTA can still be restored. Old stage
completion JSONs are historical records, not current integrity guarantees. Source
annotations and new helpers can also invalidate original code signatures.

## Offline report and tests

```
python3 scripts/build_report.py
python3 scripts/validate_repository.py
bash tests/test_pipeline.sh
```

New test logs go to logs/verification/ and reports to reports/verification/.
Original HPC validation is in provenance/hpc_validation_20261017/. An assertion
that a mock passed must never be described as real alignment or scheduler execution.

## Recreate read-based analysis on HPC

Recreate each environment on Linux from YAML; do not copy a compiled environment.
Review config/config.yaml, config/hpc_resources.yaml and reference-selection TSVs.
Set database paths, environment prefix and queue/resources for your cluster.

```
bash hpc/install_hpc_environment.sh
bash hpc/check_hpc_environment.sh
bash hpc/environment_exec.sh contamination bash scripts/01_download_data.sh
# Run remaining expensive steps through PBS, or inside an allocated compute job:
bash hpc/environment_exec.sh contamination bash scripts/02_read_qc.sh
bash hpc/environment_exec.sh contamination bash scripts/03_subsample.sh --pairs 100000
bash hpc/submit_pipeline.sh --dry-run --skip-download
```

For original screening only, use the existing-screen PBS wrapper with queue large
and 96GB for the ~78GiB index. Configure resources before submitting. For selected
validation: reference retrieval, mapping, coverage, then detection-table generation.
References excluded from the curated copy must be downloaded again from their
versioned accessions before mapping. Keep new outputs in a fresh results directory
when comparing methods rather than overwriting retained scientific evidence.

## Recreate assembly branches

```
bash hpc/install_dna_spades.sh
bash hpc/install_blobtoolkit.sh
bash hpc/submit_dna_denovo.sh
bash hpc/install_rnaspades.sh
bash hpc/submit_rna_assembly.sh
```

These are compute submissions; missing FASTQ inputs will fail. For the published
assembly branch retrieve/reuse the configured host reference, then submit via
hpc/submit_assembly_analysis.sh. Full stage commands and resource limits are in
docs/11_assembly_analysis.md, docs/12_rna_assembly.md and docs/13_dna_denovo.md.
FCS-GX for the original readset assembly branches remains optional and unverified; its special-queue memory syntax needs
administrator guidance before a new submission. No FCS database is bundled.

## GitHub

The repository root is suitable for GitHub Pages (`index.html`) if you choose to
enable it. All report images are embedded. Large regenerated sequence inputs and
intermediates are ignored; final compressed de novo assemblies and evidence are
retained. Run the repository validator before git add. No remote/push is performed
by analysis, cleanup or report scripts. Every directory outside .git has a README.


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
