# Quickstart

## View the completed analysis

Open `index.html` in a browser. It contains the workflow, results, limitations,
execution history, and seven embedded figures, including all three blobplots.
GitHub preview shows source; download HTML or use GitHub Pages to render it.

## Validate or regenerate offline

```
python3 scripts/build_report.py
python3 scripts/validate_repository.py
bash tests/test_pipeline.sh
```

No raw reads or bioinformatics installations are needed for these commands.
Tests generate tiny synthetic fixtures and keep new reports under
`reports/verification/`, separate from historical HPC evidence.

## Restore the final de novo FASTAs

```
python3 scripts/restore_artifacts.py --list
python3 scripts/restore_artifacts.py
```

Restoration checks compressed and uncompressed hashes and refuses to overwrite
modified sequences. Raw/cleaned FASTQs and reference genomes require retrieval
again before new analysis. See [the repository guide](docs/14_repository_guide.md)
for full HPC commands, branch definitions and current resource limitations.


## Supplied FCS genome: offline evidence and Linux rerun

```bash
python3 scripts/fcs_analysis.py inspect
python3 scripts/fcs_analysis.py summarize
```

The completed HPC case is independent of the two readsets. Configure an external
container/database to rerun; see [portable Linux instructions](docs/15_fcs_linux.md).
The user reports NCBI had flagged this assembly as contaminated; exact wording
was not independently retrieved.
