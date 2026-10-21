> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# Optional DNA assembly extension

This extension assesses the published assembly GCA_023334035.1 of
Globisporangium okanoganense CBS 315.81, BioSample SAMN13878593, linked to
SRR15309490. It cannot recover contaminants omitted during assembly/curation.
The existing reference FASTA is reused, or retrieved using the existing NCBI
assembly download implementation. Original reference metadata records provenance.
No original analysis scripts, configurations or results are replaced by this update.

## Plan and tool choices

1. `assembly`: reuse/download exact genome; validate FASTA, index and record SHA256.
2. `mapping`: minimap2 short-read mode maps full cleaned DNA pairs efficiently;
   SAMtools sorts, filters primary nonduplicate/non-QC-failed alignments at MAPQ20,
   and provides mean contig depth including uncovered positions. No duplicate
   marking is performed. Coverage counts aligned read bases (mate overlaps retained),
   unlike the earlier mate-overlap-removed candidate depth; keep metrics separate.
   Resources: 4 CPUs, 16 GB, 8 hours conservative limit.
3. `taxonomy`: Kraken2 classifies assembly contigs against the existing pluspf DB,
   avoiding another taxonomy database download. These are whole-contig screening
   labels, not BLAST bestsum taxonomy or independently confirmed contaminations.
   Whole-contig labels can miss internal chimeric segments.
   Resources: 4 CPUs, 115 GB, 4 hours; database inventory recorded.
4. `blobtoolkit`: BlobToolKit v4 imports assembly sequence statistics and custom
   contig depth/taxonomy fields into a native BlobDir for interactive inspection.
   An R ggplot2 companion produces PNG/PDF GC-versus-depth blobplots without a
   headless browser. Point area reflects contig length. Log depth uses +0.001 to
   display zero coverage. GC denominator excludes non-ACGT bases; all-N is missing.
   Resources: 4 CPUs, 8 GB, 4 hours. Static figures are R-rendered, not native
   BlobToolKit viewer exports. No BUSCO or BLAST-based taxonomy is claimed.
5. `fcs`: NCBI FCS-GX screens the exact same assembly for foreign genomic segments.
   Screening/action reports are retained; no automatic cleaning is performed.
   Resources: 32 CPUs, 600 GB, 12 hours in `special`; site access must be verified.
   This is intentionally above a 500 GB queue limit to allow recommended 512 GiB
   memory plus overhead. No /dev/shm copy or database download occurs automatically.

## Source availability

All extension scripts are already included in this repository; no incremental
update installer or full-directory replacement is needed. Use the commands below
with the existing directory layout.

## Inspect before installation or submission

```
bash hpc/environment_exec.sh contamination bash scripts/14_assembly_analysis.sh inspect
module avail 2>&1 | grep -Ei 'fcs|singularity|apptainer|blob'
find /datasets -maxdepth 5 -type f \( -name all.gxi -o -name 'fcs-gx*.sif' -o -name fcs.py \) -print 2>/dev/null
```

## Install optional BlobToolKit and prepare assembly

Review `environments/blobtoolkit.yml`. A separate environment avoids changing the
working contamination environment. It can include viewer dependencies; use an
existing site BlobToolKit module by configuring `blobtools_command` instead.

```
bash hpc/install_blobtoolkit.sh
bash hpc/environment_exec.sh contamination bash scripts/14_assembly_analysis.sh assembly
python3 -m unittest discover -s tests -p test_assembly_extension.py
bash hpc/submit_assembly_analysis.sh
```

The submission script queues mapping and taxonomy, then BlobToolKit only after
both succeed. It deliberately leaves FCS opt-in until its external paths are set.
Individual jobs: `qsub -o "$PWD/logs/pbs" hpc/pbs/assembly_mapping.pbs` etc.
Resources and queue can be overridden with qsub arguments. Submit from root;
`PBS_O_WORKDIR` is handled. For alternate config export ASSEMBLY_CONFIG and pass
it through `qsub -v ASSEMBLY_CONFIG=...` for individual jobs.

## FCS-GX setup

Configure `fcs_runner` (NCBI fcs.py), `fcs_image` (local .sif), and `fcs_db`
(directory with all.gxi, all.gxs, all.taxa.tsv and accompanying DB files) in
`config/assembly_analysis.json`. External paths are allowed; paths with spaces
are rejected because the upstream runner splits forwarded arguments. Load
Singularity through OOMYCETE_ENV_INIT/site modules. The NCBI v0.5.5 runner selects
Singularity from the .sif suffix and invokes an executable named `singularity`.
An Apptainer-only site needs its compatibility command or a site-approved wrapper.

Retrieve the small runner only if absent:
`curl -fL https://raw.githubusercontent.com/ncbi/fcs/v0.5.5/dist/fcs.py -o /YOUR/TOOLS/fcs.py`

Do not start a new ~470 GiB database download before checking site installations
and storage/permission. Container download is also explicit. The config defaults
are blank so missing setup stops with a clear error, rather than downloading.

Once prepared:
```
qsub -o "$PWD/logs/pbs" hpc/pbs/assembly_fcs.pbs
```

## Outputs, restart and verification

All new evidence is under `results/DNA/07_assembly/DNA_Gokan_CBS315_81/`:
`assembly_manifest.json`, `DNA.full_cleaned.filtered.bam` and index,
`samtools_coverage.tsv`, `assembly.kraken.tsv`, `assembly.kraken.report.tsv`,
`contig_evidence.tsv`, `blobdir/`, `assembly_blobplot.png/pdf`, `fcs_gx/`.
Logs: `logs/DNA/14_assembly_*`, scheduler logs: `logs/pbs/`.

Stages record signatures and SHA256 output checksums. The full BAM/reads and FCS
image are hashed, which incurs I/O. Large shared database files use recorded
sizes/mtimes; that inventory is not an integrity checksum. Unchanged completed
stages skip. Review stale outputs before explicit `--force`; an incomplete
BlobDir or FCS directory must be moved aside before retry. The source assembly
is never cleaned automatically. Keep result interpretation separate from the
read-based detections table until reviewed. Adding Python files can invalidate
older pipeline signatures; do not rerun completed read-based stages unnecessarily.

## Verification status

Local control/data tests and Bash/Python syntax are tested separately in
`reports/assembly_extension_validation.md`. No real BlobToolKit install, mapping,
FCS database screening, or live PBS submission is claimed until run on HPC.

Sources: [NCBI FCS-GX](https://github.com/ncbi/fcs/wiki/FCS-GX-quickstart),
[BlobToolKit dataset creation](https://blobtoolkit.genomehubs.org/blobtools2/blobtools2-tutorials/creating-a-dataset/),
[custom data import](https://github.com/genomehubs/blobtoolkit/blob/main/src/blobtools/lib/add.py).


Additional case: [the independent FCS public-genome analysis](../reports/fcs_analysis.md) documents GCA_051997085.1, selected because the user reports an NCBI contamination flag. It is separate from the original SRA readsets and does not change the measurements above.
