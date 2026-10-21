> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# De novo DNA assembly and contig screening

This optional branch assembles the full cleaned DNA_Gokan_CBS315_81 read pairs
(SRR15309490) from scratch. No published genome FASTA, trusted contigs, or other
reference-guided sequence is passed to SPAdes. It is independent of the completed
published-assembly branch, the RNA transcript branch and the original screening.

## Plan and tools

1. Standard DNA SPAdes 4.2 assembles paired short WGS reads. Keep automatic k-mers
   and default error correction. No --rna, --meta, --careful, or high-coverage
   --isolate assumption is imposed; low-abundance non-target assembly recovery is
   an exploratory goal. Use contigs.fasta, retaining the assembler's contig output
   without an additional length/coverage filter. This is a screening assembly,
   not a claim of a complete/polished oomycete genome. Low-coverage contaminants
   can fail to assemble, so read-based screening remains complementary.
2. minimap2 -ax sr maps the same full cleaned DNA mates to these new contigs.
   SAMtools sorts and filters primary alignments at MAPQ20, excluding flags3844,
   and computes contig mean depth/breadth including uncovered bases. Duplicate
   marking is not performed; only existing duplicate flags are excluded. Overlap
   of retained mates contributes twice to these assembly depth metrics, unlike
   the earlier candidate coverage calculation. Do not treat the two as identical.
3. Kraken2 labels the newly assembled contigs using /datasets/unzipped/pluspf.
   Labels are provisional contig classifications, not validated organism claims.
4. BlobToolKit creates a native BlobDir with GC, length, mapping depth and custom
   Kraken label fields. R renders PNG/PDF blobplots; no browser is required for
   static output. Standard taxonomic bestsum/BLAST inference is not claimed.
5. Optional FCS-GX screens the NEW contigs using target taxid182683. It reuses only
   software and database settings from config/assembly_analysis.json; the published
   assembly path is never reused as an input. No automatic sequence removal occurs.

## Files and resources

Configuration: config/dna_denovo.json. Default result directory:
results/DNA/08_denovo/DNA_Gokan_CBS315_81/.

| Stage | Resources | Main outputs |
|---|---|---|
| assemble | large, 8 CPUs, 64 GB, 24 h; SPAdes cap56 GB | spades/contigs.fasta, spades.log, params.txt, denovo_manifest.json with N50 |
| mapping | medium, 4 CPUs, 16 GB, 8 h | filtered BAM/index and samtools_coverage.tsv |
| taxonomy | large, 4 CPUs, 115 GB, 4 h | assembly.kraken.tsv and report |
| blobtoolkit | medium, 4 CPUs, 8 GB, 4 h | contig_evidence.tsv, blobdir/, dna_denovo_blobplot.png/pdf |
| optional fcs | special, 32 CPUs, 600 GB, 12 h | fcs_gx/ reports |

These are initial limits, not measured performance. Startup free-disk reserve40
GiB is configurable and does not guarantee intermediate storage sufficiency.
All paths resolve relative to the project root unless configured externally.
Taxonomy DB files are inventoried by size/mtime, not rehashed every execution.
Read/assembly/output checksums and parameters control reproducible stage skipping.
Logs: logs/DNA/16_dna_denovo_STAGE_DNA_Gokan_CBS315_81.log and logs/pbs/.

## Apply and execute without replacing the project

All source scripts are included in this repository; no update installer is needed.

```
bash hpc/install_dna_spades.sh
bash hpc/environment_exec.sh contamination bash scripts/16_dna_denovo.sh inspect
python3 -m unittest discover -s tests -p test_dna_denovo_extension.py
bash hpc/submit_dna_denovo.sh
qstat -u "$USER"
```

The SPAdes installer reuses the identical rnaspades environment prefix if the RNA
branch has already installed it; otherwise it creates that environment using
its own environments/dna_spades.yml. DNA and RNA assembly jobs invoke different
modes and use distinct input and output directories. BlobToolKit uses the existing
DNA extension helper/environment. Existing analysis configuration is preserved.

Submission graph: assembly -> mapping and taxonomy in parallel -> BlobToolKit.
Downstream jobs use afterok dependencies. Individual entry points support --help:

```
bash hpc/environment_exec.sh contamination bash scripts/16_dna_denovo.sh assemble
bash hpc/environment_exec.sh contamination bash scripts/16_dna_denovo.sh mapping
bash hpc/environment_exec.sh contamination bash scripts/16_dna_denovo.sh taxonomy
bash hpc/environment_exec.sh contamination bash scripts/16_dna_denovo.sh blobtoolkit
```

Use PBS wrappers for compute work, not the login node. The default submit helper
uses the shipped config. For an alternate config submit individual PBS wrappers
with `-v DNA_DENOVO_CONFIG=config/YOUR_CONFIG.json` and appropriate dependencies.

## Optional FCS-GX

FCS is not submitted by the default helper because site memory hook errors for
special queue have not been resolved. Once the administrator confirms an accepted
resource syntax and software/database paths are set, use:

```
qsub -o "$PWD/logs/pbs" hpc/pbs/dna_denovo_fcs.pbs
```

Submit after the assembly completes successfully. This wrapper screens only
spades/contigs.fasta from this branch. No ~470GiB database download is performed.
Do not lower the allocation merely to bypass the known submission-hook failure.

## Resume

An interrupted SPAdes stage requires --resume, identical validated read pairs,
thread/memory options and commands; the assembler is called with --continue.

```
qsub -v DNA_RESUME=1 -o "$PWD/logs/pbs" hpc/pbs/dna_denovo_assemble.pbs
```

Inspect previously submitted held jobs to avoid duplicates. An existing output
folder without valid checkpoint metadata is refused. Move old outputs aside for
review rather than silently overwriting. Completed stages skip with verified
output checksums. New Python files can invalidate prior pipeline signatures;
there is no need to rerun old read-based analyses.

## Interpretation and verification

Compare this assembly's GC/depth/taxonomy structure with the published assembly,
but do not infer organism presence from a coloured point alone. Missing contigs
can reflect low read coverage or assembly choices. FCS actions also require review.
Raw new assembly N50 is descriptive, not proof of correctness. Final significance
bins and source judgments remain the student's decisions.

Local tests use mock assembler/FCS/scheduler calls, verifying DNA mode, no reference
input, input checks, resume, skip, summary statistics, dependencies, and exact FCS
input selection. Real assembly and live PBS execution remain pending on HPC.

Sources: [SPAdes parameters](https://ablab.github.io/spades/datatypes.html),
[SPAdes modes](https://ablab.github.io/spades/running.html),
[NCBI FCS-GX](https://github.com/ncbi/fcs/wiki/FCS-GX-quickstart).
