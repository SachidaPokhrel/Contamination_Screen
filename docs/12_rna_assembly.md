> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# RNA transcript assembly and BlobToolKit

This optional branch assembles the full cleaned paired reads from
RNA_Phib_mycelia1 (SRR16206986, Phytophthora hibernalis). It does not use the
100,000-pair subsample and does not modify the completed DNA, FCS, or read-based
results. No new sequencing data or taxonomy database downloads are required.

## Tools and scientific choices

- rnaSPAdes (SPAdes 4.2) assembles eukaryotic RNA transcripts while accommodating
  uneven expression; install it in a separate environment to preserve working
  environments. Invoke `spades.py --rna`, keeping the recommended automatic k-mers.
- Library strand-specificity is unverified; no `--ss` flag is inferred. Config
  allows `fr` or `rf` only if library metadata supports it. These flags describe
  transcript strandedness, not paired-read orientation.
- Use the main `transcripts.fasta` output, not only highly expressed hard-filtered
  transcripts, to retain possible low-expression associates.
- minimap2 `-ax sr` aligns full cleaned RNA pairs to assembled transcripts. No
  splice-aware alignment is needed against transcript sequences. SAMtools retains
  primary alignments with MAPQ >=20, excludes flags 3844, indexes the BAM and
  calculates per-contig mean depth including uncovered bases. Flagged duplicates
  are excluded but duplicate marking is not performed; mate overlaps contribute
  to these assembly-depth measurements. Isoforms/repeats may lose MAPQ-filtered
  support; this is exploratory coverage, not TPM or a cell-abundance estimate.
- Kraken2 labels transcript sequences using the existing pluspf database. Database
  coverage is incomplete; transcript taxonomy is provisional. Bracken is not run
  on transcript contigs because its read-length model does not match that input.
- BlobToolKit creates a native BlobDir with GC, length, custom mapped-depth and
  Kraken label fields. R ggplot2 renders static PNG/PDF companions, as for DNA.
  Point area represents transcript length; depth+0.001 is plotted on a log scale
  to retain zero coverage. Unknown GC for all-N sequences is left missing.

## Plan, resources and paths

| Stage | Inputs | Outputs | PBS resources |
|---|---|---|---|
| assemble | full cleaned RNA mates | rnaspades/transcripts.fasta, logs, parameters, manifest | large, 8 CPUs, 64 GB, 24 h; assembler cap 56 GB |
| mapping | transcripts, same RNA mates | RNA.full_cleaned.filtered.bam, index, samtools_coverage.tsv | medium, 4 CPUs, 16 GB, 8 h |
| taxonomy | transcripts, pluspf | assembly.kraken.tsv and report | large, 4 CPUs, 115 GB, 4 h |
| blobtoolkit | transcripts, coverage, assignments | contig_evidence.tsv, blobdir, rna_blobplot.png/pdf | medium, 4 CPUs, 8 GB, 4 h |

Limits are initial conservative estimates, not measured resource requirements.
The configured minimum 40 GiB free disk is a startup reserve, not a guarantee of
sufficient space for all intermediates. Outputs default to
`results/RNA/08_transcriptome/RNA_Phib_mycelia1/`. Logs use
`logs/RNA/15_rna_STAGE_RNA_Phib_mycelia1.log`, plus logs/pbs scheduler output.
Configuration: `config/rna_assembly.json`; scripts resolve project root dynamically.
Edit resource requests in the four `hpc/pbs/rna_*.pbs` files, or override via qsub.
Keep assembler `spades_memory_gb` below requested memory with headroom.

## Execute the included RNA branch

The source scripts and environment recipes are already included. Recreate the
optional environment, inspect missing raw inputs, and submit through PBS:

```
bash hpc/install_rnaspades.sh
bash hpc/environment_exec.sh contamination bash scripts/15_rna_assembly.sh inspect
python3 -m unittest discover -s tests -p test_rna_extension.py
bash hpc/submit_rna_assembly.sh
qstat -u "$USER"
```

Submission graph: assemble -> mapping and taxonomy -> BlobToolKit (afterok of both).
A failed upstream stage must not release downstream jobs. Individual entry points:

```
bash hpc/environment_exec.sh contamination bash scripts/15_rna_assembly.sh assemble
bash hpc/environment_exec.sh contamination bash scripts/15_rna_assembly.sh mapping
bash hpc/environment_exec.sh contamination bash scripts/15_rna_assembly.sh taxonomy
bash hpc/environment_exec.sh contamination bash scripts/15_rna_assembly.sh blobtoolkit
```

Run resource-intensive stages on compute nodes using the PBS wrappers, not the
login node. Wrapper CPU counts override config threads for each stage. For an
alternate config submit individual wrappers with `-v RNA_ASSEMBLY_CONFIG=...`.
The convenience submission script targets the shipped default configuration.
The install script records exact platform-specific packages and verifies
`spades.py --version`; compiled environments are recreated on each platform.

## Restart and validation

Completed stage signatures and output SHA256 checksums control skipping. An
interrupted rnaSPAdes run requires explicit `--resume` and identical read content,
CPU/memory options and strandedness; it uses upstream `--continue`.

```
qsub -v RNA_RESUME=1 -o "$PWD/logs/pbs" hpc/pbs/rna_assemble.pbs
```

Before re-submitting, inspect previously queued/held jobs to avoid duplicates.
Do not manually release jobs held by failed dependencies. Whole-branch re-submit
is possible with `bash hpc/submit_rna_assembly.sh --resume`, after resolving old
jobs. A genuine restart from scratch requires moving the old rnaspades directory
and affected results aside for review, not silently overwriting. Stale locks
require confirming no process is active before removal. Biomass, infection, or
source categories are not inferred from these plots. No DIAMOND/viral protein
search or viral validation is included in this branch yet.

## Sources

[RNA assembly and output](https://ablab.github.io/spades/rna.html),
[SPAdes invocation](https://ablab.github.io/spades/running.html),
[BlobToolKit custom fields](https://github.com/genomehubs/blobtoolkit/blob/main/src/blobtools/lib/add.py).
