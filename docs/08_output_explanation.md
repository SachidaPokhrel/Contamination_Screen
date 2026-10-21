> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# Stages, commands and outputs

Run from the root. This helper uses the recreated main environment without persistent shell activation:
```bash
run() { bash hpc/environment_exec.sh contamination "$@"; }
run bash scripts/00_check_environment.sh --strict
run bash scripts/01_download_data.sh
run bash scripts/02_read_qc.sh
run bash scripts/03_subsample.sh --pairs 100000
run bash scripts/04_kraken2_screen.sh
run bash scripts/05_bracken_abundance.sh
run python scripts/06_select_candidates.py
# Manual candidate/reference configuration is required here.
run bash scripts/07_download_references.sh
run bash scripts/08_mapping.sh
run bash scripts/09_coverage.sh
run bash scripts/10_rna_virus_screen.sh
run python scripts/11_detection_table.py
bash hpc/environment_exec.sh plotting Rscript scripts/12_visualization.R
run python scripts/13_generate_report.py
```

All Bash/Python analysis entry points share --config PATH, --sample SAMPLE, --force and --help; stage-specific arguments are described by --help. The R script reads config/config.yaml (or --config) and accepts --table, --results, --output and --force. Paths in config resolve against the project root, independent of caller working directory. Environment prefix and scratch can be external. Shared implementation resides in common.py and pipeline.py; numbered scripts are real executable entry points, not empty placeholders.

## Important files
| Location | Content |
|---|---|
| data/ASSAY/sra/RUN/ | Validated SRA archive retained for provenance/resumption. |
| data/ASSAY/raw/SAMPLE_1.fastq.gz and _2 | Verified paired reads, checksum manifest, download.json and completion signature. |
| metadata/download_manifest.tsv | Run, sample, file, SHA256, compressed bytes and verification time. |
| results/ASSAY/01_qc/SAMPLE/ | Raw/clean FastQC reports, fastp HTML/JSON, paired-read counts. |
| data/ASSAY/cleaned/ and subsampled/ | Cleaned pairs and fixed-seed subsample pairs with provenance. |
| results/ASSAY/02_kraken2/SAMPLE/ | Kraken assignments, standard six-column report and database/readset metadata. Paired classification counts represent fragments/spots. |
| results/ASSAY/03_bracken/SAMPLE/ | Bracken abundance and report, or explicit disabled status. |
| results/ASSAY/04_candidates/SAMPLE/ | Ranked species candidates, expected-target labels, evidence flags and selection template. |
| references/{host,candidates,viral}/ | User-selected versioned FASTA plus metadata, checksums and FASTA index. |
| results/ASSAY/05_mapping/SAMPLE/MODE/ | Combined labeled reference/contig ownership table, Bowtie2 index, sorted indexed BAM, flagstat/stats and exact input denominator metadata. |
| results/ASSAY/06_coverage/SAMPLE/MODE/ | Filtered indexed BAM, coverage.tsv, compressed full-position profile and threshold definitions. |
| results/RNA/07_viruses/SAMPLE/ | Reference-supported viral metrics, explicit evaluated-reference status and optional assembly/protein hits. |
| tables/detections.tsv and .csv | Joined candidate evidence; header-only templates until biological analysis runs. |
| figures/ | PNG at 300 dpi and PDF plots; generated only when R runs successfully. |
| reports/*_report.md | One-page calculated report template; user interpretation is not generated. |
| *.done.json | Code/input/config signature, output checksums and completion time; verified before a skip. |
| logs/ | Per-step live command/version/error logs; PBS spool/runtime logs are under logs/pbs. |
| reports/synthetic_demo/ | Clearly labeled executed synthetic fixtures and derived demonstration outputs; never biological detections. |

MODE is candidate_only (all reviewed candidates jointly) or competitive (relevant host references plus candidates). Numbered result directories contain sample subdirectories so multiple samples cannot overwrite each other.

## Detection table columns
| Column(s) | Definition |
|---|---|
| sample_id, assay, reference_id, taxid, organism, role | Stable sample and reference ownership keys; role candidate/viral/host. Host rows are omitted from final detections. |
| mapping_mode, readset | Alignment context and exact raw/cleaned/subsampled input. |
| supporting_reads | Primary mapped sequencing-read alignments passing flags/MAPQ; both mates count as two reads. |
| supporting_fragments | Distinct read-pair names with either mate supporting that reference. |
| input_reads, input_fragments | All biological reads (2×pairs) and pairs in the exact validated input readset. |
| read_fraction_percent, fragment_fraction_percent | 100 × supporting count / corresponding full-input count. |
| reference_length | Full sum of contig lengths for that reference. |
| depth_sum | Sum of retained aligned-base depths over all reference positions. |
| mean_depth | depth_sum / reference_length; zeros included. |
| covered_bases, bases_5x, bases_10x | Positions reaching ≥1, ≥5 and ≥10 retained-base coverage. |
| breadth_1x_percent, breadth_5x_percent, breadth_10x_percent | 100 × threshold-covered bases / full reference length. |
| mean_mapq, median_mapq | Read-weighted summaries among retained primary alignments; blank if no support. |
| min_mapq, min_baseq, excluded_flags, mapq_255_excluded | Explicit alignment/base-quality definitions. |
| mate_overlap_removed_for_depth, fragment_policy, duplicate_policy | Overlapping mates counted once for depth by default; fragment either-mate policy; only preflagged duplicates excluded. |
| rna_reference_warning | Warning that genomic RNA host competition is not splice-aware. |
| kraken_percent, kraken_clade_fragments, screening_flags | Screening hypotheses and flags; blank if reference taxid absent from ranked species rows. |
| bracken_estimated_fragments, bracken_fraction, bracken_read_length | Optional database-model estimates; paired Kraken inputs imply assignment/fragment units, not observed mapped reads. |
| database_release, taxonomy_date, evidence_status | Database provenance and reference-alignment evaluation status. Unknown values remain explicit. |
| significance_bin, likely_source, scientific_interpretation, evidence_supporting_interpretation | Student-editable judgments. Existing values are preserved on rerun by sample/reference/mode/readset key. |

config/references.tsv accepts role host/candidate/viral, optional assay DNA/RNA/all for host applicability, versioned nucleotide accessions separated by semicolons or one versioned GCA/GCF assembly, local uncompressed FASTA destination, evidence URL and verified=true. Assembly downloads resolve exact versions through NCBI Assembly metadata; no FTP hierarchy is guessed. A local verified FASTA can have blank accessions with source documentation. Candidate_selection.tsv links sample/taxid/reference_id and selected=true; taxids must agree with reference rows. RNA host transcriptome accessions/FASTA can replace the provided genomic lead.

Bracken is disabled by default: first verify databaseREADLENGTHmers.kmer_distrib and the empirical read-length distribution. The configured 100 nt model is not claimed correct for every candidate dataset. Quality trimming can create variable lengths; document any approximation. Optional protein-search hits have no automatic source/significance classification and require reviewed reference remapping to enter the final table.
