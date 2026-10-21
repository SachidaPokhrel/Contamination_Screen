# Run FCS-GX on another Linux system

The supplied `fcs/5screen.sh` and `fcs/clean.sh` now invoke the annotated,
Python-standard-library runner `scripts/fcs_analysis.py`. They need no module
system, PBS, Conda or hardcoded cluster paths. Original scripts are archived
in `provenance/fcs_original/`. Historical FASTAs/reports are never overwritten.
Python 3.10+ and one installed container runtime are required for a rerun.

## Inspect and reproduce the offline summaries

Run from the repository root (script entry points also detect the root when
invoked by absolute path from another directory):

```bash
python3 scripts/fcs_analysis.py inspect
python3 scripts/fcs_analysis.py summarize
python3 scripts/build_report.py
```

## Screen with an existing local container and database

Configure `fcs/config.json`, use the flags below, or set `FCS_IMAGE` and `FCS_DB`.
Replace the example external paths with paths on your Linux machine. Reuse a
compatible NCBI FCS-GX database and image; neither is downloaded automatically.
Container runtime permission and enough memory/disk must be provided by your
system. Database size is hundreds of GB. High memory improves performance;
the historical 40 GB allocation is not a performance guarantee.

```bash
bash fcs/5screen.sh --engine apptainer \
  --image /path/to/fcs-gx.sif --db /path/to/gxdb \
  --threads 8 --output-dir fcs/reruns/linux_case --dry-run
bash fcs/5screen.sh --engine apptainer \
  --image /path/to/fcs-gx.sif --db /path/to/gxdb \
  --threads 8 --output-dir fcs/reruns/linux_case
bash fcs/clean.sh --engine apptainer \
  --image /path/to/fcs-gx.sif --threads 8 \
  --output-dir fcs/reruns/linux_case
```

Use `--engine singularity` for Singularity. Docker/Podman accept an already
present image name with `--engine docker --image YOUR_LOCAL_IMAGE`; automatic
pulling is disabled. The runner uses the NCBI image entry points
`python3 /app/bin/run_gx` and `/app/bin/gx clean-genome`. Verify these paths if
using a differently packaged image. Inputs/database are bound read-only;
new outputs are writable. Cleaning streams plain or gzip FASTA through stdin.
Paths with spaces are supported; container mount paths containing colon,
comma or newline are rejected explicitly. Positive taxid/thread settings are required.

To clean against the original supplied action report instead of a new screen:

```bash
bash fcs/clean.sh --engine apptainer --image /path/to/fcs-gx.sif \
  --output-dir fcs/reruns/reclean \
  --action-report fcs/decontamination/GCA_051997085.1.36331.fcs_gx_report.txt
```

Each stage requires a fresh stage-output directory. An interrupted/nonempty run
is protected: inspect its log, then choose a new output root. Logs stream during
execution; manifests record commands, input/output hashes and local image hash
or image name. Database inventory records sizes/mtimes, not full database hashes.
Use a versioned/digest-pinned Docker image for reproducibility.

## Optional PBS

`hpc/pbs/fcs_public_genome.pbs` is an optional wrapper. Set `FCS_IMAGE`, `FCS_DB`
and runtime in your job environment, then request resources/queue valid at your
site. Run directly on an appropriately provisioned Linux workstation/server
without qsub by using the commands above. No new PBS submission was tested here.

## Metadata and interpretation

`python3 scripts/verify_fcs_ncbi.py --help` describes optional, cached online
NCBI verification. Network access is needed; assembly/sample linkage was
verified from the NCBI project table, but exact contamination-flag wording and
an associated SRA run remain unresolved. See `reports/fcs_analysis.md`.
Portable command construction and offline auditing are locally testable;
the new container launcher has not been exercised with a real image locally.

Container entry points follow the [NCBI FCS launcher source](https://github.com/ncbi/fcs/blob/main/dist/fcs.py). Image compatibility must still be verified for the selected release.
