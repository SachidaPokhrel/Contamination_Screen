> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# Troubleshooting

| Failure | Action |
|---|---|
| No manager / cannot resolve DNS | Installation was not completed. Load a supported Conda/Mamba module or install a manager on a network-enabled machine; verify shell HTTPS access. Browsing-service access does not prove shell connectivity. |
| Environment solve fails | YAMLs are not locally solved lockfiles. Check channel/platform availability and memory; adjust reviewed compatible version constraints and retain solver logs. Recreate on target Linux. |
| No matching samples | Check enabled=true, TSV tabs, unique sample IDs, DNA/RNA assay labels and --sample spelling. |
| Download disabled | Review run-level metadata and size, obtain download approval, then enable allow_data_download. No automatic override is performed. |
| fasterq-dump runs out of space | Point scratch_dir at disk-backed space; /tmp can be tmpfs. Inspect available space and increase reserve factor for the actual run. prefetch resumes existing archives; incomplete conversion is rerun. |
| FASTQ mismatch/truncation | Preserve raw files, inspect conversion/download log and checksums, validate archive; do not truncate one mate to match the other. |
| Missing Kraken index / too little RAM | Set kraken_db or KRAKEN2_DB to an appropriate prepared database with three nonempty .k2d files. Subsampling does not shrink database RAM needs. |
| Bracken distribution missing | Use a compatible distribution/read length, prepare with the matching database, or keep Bracken disabled. Do not substitute an unrelated distribution. |
| No selected candidates | Review stage 06 ranked TSV, append verified reference metadata, select explicitly in config/candidate_selection.tsv. Empty viral output is not a negative virus result. |
| Assembly accession unresolved | Verify exact version on NCBI Assembly; retain metadata responses. A WGS master record does not itself contain the assembly's contig sequences. |
| Missing SAMtools/Bowtie2 | Use environment_exec.sh contamination; rerun real mapping test. Pure-Python fixture tests do not install or validate these tools. |
| Stale/modified output | Compare config/input/code changes and output checksums. Use the relevant --force only after review. Never bypass a mismatch by simply relabeling output. |
| Stage locked | Confirm the matching process or PBS job is no longer running; then remove only its stale .lock file and rerun. |
| PBS cannot find root | Submit from project directory or export OOMYCETE_PROJECT_ROOT with qsub -v. A PBS spool copy is not the project location. |
| PBS rejects resource directive | Check PBS Pro/OpenPBS select versus Torque nodes syntax and queue policy. Helper supports resource_style=nodes; individually submitted wrappers need explicit qsub resource overrides. |
| afterok jobs held | Inspect failed upstream logs and site scheduling rules; resubmit fixed stage and remaining downstream jobs. A failed chain should not run downstream automatically. |
| R output already exists | Preserve reviewed figures or explicitly use --force. R execution/parse was not locally tested without Rscript. |
| Report already exists | Edit the existing report; --force explicitly regenerates it and overwrites edits. TSV interpretation columns are preserved by stable key separately. |
| Few RNA reads in host competition | Supply host transcriptome; Bowtie2 genomic mapping misses exon-spanning reads. Reference divergence and incomplete transcripts also matter. |

All analysis logs are live; inspect logs/ASSAY/stage_SAMPLE.log and outer stage logs. Completion signatures include code and the full configuration, so even an unrelated configuration change can conservatively require a rebuild. This is deliberate provenance behavior; split configuration files by separate project copy if independent analyses require different settings.
