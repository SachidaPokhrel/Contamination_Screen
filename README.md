# Oomycete contamination analysis

A reproducible record of contamination screening and assembly assessment for one
DNA whole-genome sequencing readset and one independent RNA-seq readset. This
repository contains the actual HPC result tables, figures, native BlobToolKit
datasets, compressed final assemblies, annotated analysis code, environment
specifications, PBS jobs, and execution logs.

**Start with [the complete HTML report](index.html).** Open it in a browser after
downloading: all three blobplots and four other evidence figures are embedded,
so the report can also be shared as a single offline file. GitHub's file preview
displays HTML source; use a local browser or enable GitHub Pages to render it.

[Final decision Word document](reports/final_decisions.docx) · [What ran and what it means](reports/analysis_summary.md) · [Interpretation guide](reports/interpretation_guide.md)

[Quickstart](QUICKSTART.md) · [Methods](docs/10_methods.md) ·
[Detection table](tables/detections.tsv) · [Repository guide](docs/14_repository_guide.md) ·
[Verification](reports/repository_validation.md) · [One-page writeup](reports/one_page_writeup.md)

## Scientific question

Which non-target assignments are supported by independent reference mapping and
coverage, and which remain ambiguous after examining conserved sequence and
alternative taxonomic matches? Kraken2/Bracken labels are hypotheses; they are
not sufficient evidence of contamination, organism identity, or biological source.

| Dataset | Organism / sample | SRA run | BioProject | BioSample |
|---|---|---|---|---|
| DNA WGS | Globisporangium okanoganense CBS 315.81 | SRR15309490 | PRJNA601986 | SAMN13878593 |
| RNA-seq | Phytophthora hibernalis, Phibe_mycelia1 | SRR16206986 | PRJNA746351 | SAMN22065162 |
| Additional FCS genome: GCA_051997085.1 | Globisporangium irregulare strain 13-30 | Not verified; assembly-only analysis | PRJNA816194 | SAMN26664723 |

The two readsets are **different species and isolates**, not matched DNA/RNA observations.
The additional FCS genome is a third independent case, selected because the user reports an NCBI contamination flag (exact wording not independently retrieved). See [dataset descriptions](docs/02_dataset_selection.md) and [all analysed datasets](metadata/analysis_datasets.tsv).
Both readsets are cultured isolates; a field-collected origin or RNA-virus infection was
not established. See [metadata](metadata/selected_datasets.tsv) for source records
and the distinction between known metadata and unresolved selection preferences.

## What was actually executed

1. SRA download using prefetch, vdb-validate, fasterq-dump and compression.
2. FastQC and paired fastp QC. DNA: 5,888,715 input pairs, 5,685,476 retained.
   RNA: 6,040,967 input pairs, 5,941,455 retained.
3. Seeded subsampling to **100,000 pairs per sample** for read-based screening.
4. Kraken2 classification against the original shared database; manually selected
   reference retrieval; candidate-only and competitive Bowtie2 mapping; SAMtools
   depth, breadth, primary-read and distinct-fragment measurements.
5. A second RNA reference-validation round and targeted rRNA/tRNA/BLAST specificity
   checks. Final measurements contain 16 rows: DNA three references and RNA five,
   each in candidate-only and competitive modes.
6. A separate **pluspf Kraken2–Bracken** comparison on the same subsamples, using
   150 bp DNA and 100 bp RNA distributions. The latter approximates ~90 bp reads.
7. Three completed assembly/BlobToolKit analyses:
   - published same-isolate DNA assembly GCA_023334035.1, mapped with full DNA reads;
   - independent SPAdes DNA assembly from the full cleaned reads;
   - rnaSPAdes transcript assembly from the full cleaned RNA reads.
8. Native BlobDirs plus R-rendered GC/depth/taxonomy plots and final evidence figures.

### Principal findings

- **Pseudomonas CIP-10 was not independently validated.** Competitive mapping
  retained 143 DNA reads (0.0715% of input reads) and 128 RNA reads (0.064%). All
  DNA support and 126 RNA alignments overlapped annotated rRNA; one RNA alignment
  overlapped tRNA and one lay in sucD. Both mates of the sucD pair had Phytophthora
  transcript matches. Selected rRNA pairs also matched oomycete/eukaryotic records.
- Acetobacteroides, Tateyamaria, and the selected Stenotrophomonas reference lacked
  retained support under the filters used; these negatives do not exclude all strains.
- Miltoncostaea retained 11 RNA reads over a single 130 bp interval; specificity
  remains unresolved. An optional subsequent interval search was skipped.
- Bracken produced abundance estimates, including Bremia/human/fungal labels,
  which are **not validated detections**. Its model fraction and the percentage
  of all input pairs have different denominators; see the comparison table.
- De novo DNA: **18,388 contigs, 46,890,401 bp, N50 17,970 bp**. RNA:
  **27,606 transcripts, 26,496,841 bp**. Most assembly sequence is unclassified
  by Kraken; coloured contigs remain provisional assignments.

The assignment's noise/trace/consequential/biological bins and likely sources
remain **student decisions**. Their columns have not been automatically filled.
No database error, true human contamination, or new microbial associate is claimed.

## What was not completed

No completed FCS-GX report was supplied for the original DNA/RNA assembly branches. FCS configuration and PBS
wrappers remain available, but a special-queue memory-parsing hook rejected the
reported submissions. There is no completed viral protein search, viral validation,
CheckV assessment, or spike-in detection-limit experiment. Transcript assembly
alone is not RNA-virus discovery.

## Repository layout

| Directory | Contents |
|---|---|
| config/ | Sample/reference selection and configurations for each analysis branch |
| scripts/ | Annotated pipeline, report builder, restoration tools and specificity helpers |
| environments/ | Conda specifications and recorded Linux explicit package lists |
| hpc/ | Environment launch/install scripts, PBS jobs, dependency submission helpers |
| metadata/ | SRA/NCBI metadata, compressed-assembly hashes and cleanup inventory |
| results/ | Original read evidence and all three assembly branches |
| results_round2/ | Expanded RNA mapping/coverage results |
| results_pluspf/ | Separate pluspf screening and Bracken estimates |
| results_final/ | Relative links composing original DNA + round-two RNA evidence |
| tables/ | Primary detections, specificity audit and derived summaries |
| figures/ | Final evidence figure exports |
| reports/ | Writeup, validation, evidence notes and structured report summaries |
| provenance/ | Original validation records, transfer manifest and execution chronology |
| logs/ | Preserved HPC/tool/scheduler output, including failures and successful reruns |
| tests/ | Synthetic/mocked control tests and optional real-tool checks |
| agent/ | Actual execution record and clearly labelled transcript availability |
| data/ | Documentation only: raw and cleaned readsets are not included |
| references/ | Retrieval metadata; downloaded reference sequences are regenerable |

Every retained directory has a README explaining its role. Relative layout is
preserved to avoid breaking the stage scripts and evidence paths.

## View or regenerate results without sequencing data

Python 3.10+ is sufficient; no Conda, database, R or network is needed to build HTML:

```bash
python3 scripts/build_report.py
python3 scripts/validate_repository.py
bash tests/test_pipeline.sh
```

`index.html` is generated from actual retained TSV/JSON/log/PNG files. Primary
measurements and user interpretation columns are not overwritten by the builder.
Unit tests use tiny constructed fixtures; they do not rerun biological analyses.

## Recreate computational runs on Linux/PBS

1. Recreate environments from YAML using the hpc installers; never transfer a
   compiled environment from another machine.
2. Configure external database locations and site resource/queue settings.
3. Download the selected SRA runs and run QC/subsampling again; raw/cleaned FASTQs
   were not included in the supplied results copy.
4. Restore the retained de novo assemblies if mapping or screening needs plain FASTA:

```bash
python3 scripts/restore_artifacts.py --list
python3 scripts/restore_artifacts.py
python3 scripts/prepare_final_view.py
```

5. Run stages individually or submit the corresponding PBS helper. See
   [reproduction commands](docs/14_repository_guide.md). Old completion markers
   describe historical outputs; moved intermediates and annotated code invalidate
   some restart signatures. Review and regenerate deliberately rather than forcing
   every stage or treating archived markers as proof that missing files exist.

Original cluster paths remain in logs and historical manifests as provenance.
Runtime scripts detect the project root; shared database/environment paths are
configurable. For the original ~78 GiB Kraken index, screening requests need a
large-memory queue. The generic resource configuration now supports per-stage queues.

## GitHub preparation and curation

Raw reads, BAMs, indexes, depth tracks, corrected reads and assembler work graphs
are excluded. Final de novo FASTAs are losslessly compressed and checksummed;
all figures, BlobDirs, tables and meaningful logs remain. Removed files were moved
outside this repository into a recovery directory; the exact actions and SHA256
values are recorded in [repository_cleanup.tsv](metadata/repository_cleanup.tsv).
No scientific measurement was silently replaced or inferred during cleanup.

Before publishing:

```bash
python3 scripts/validate_repository.py
git status --short
git add .
git diff --cached --stat
# Review, commit, then push to your own repository.
```

No remote has been configured and no commit or push was performed during curation.
The HTML can be published with GitHub Pages from the repository root if desired.

## License and attribution

Pipeline code retains its MIT license. Public NCBI records, software outputs and
upstream tools retain their respective attribution/terms. See recorded NCBI
accessions and [methods](docs/10_methods.md) for tool documentation. The agent's
full chat export was unavailable; the execution history is not represented as a
verbatim transcript.


## Added public-genome FCS-GX case (2026-10-20)

The separate *Globisporangium irregulare* strain 13-30 assembly GCA_051997085.1
(PRJNA816194; SAMN26664723) was selected because **the user reports NCBI flagged
it as contaminated**; exact flag wording was not independently retrieved.
Supplied completed FCS-GX outputs recommend excluding eight fungal-labelled
contigs: 12,358 bp, 0.028973% of assembly bases. This is independent of the
original two SRA readsets; no SRA run or raw-read metrics were verified for this
additional case. Student bins/sources remain unassigned. See the
[FCS case report](reports/fcs_analysis.md) and
[portable Linux instructions](docs/15_fcs_linux.md).
