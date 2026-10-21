# PBS deployment

See [complete deployment instructions](../docs/06_hpc_execution.md). Recreate YAML environments on the Linux cluster, configure external databases/scratch and site queue/resources, validate real tools, submit screening, review candidates, then submit reference validation.

```bash
bash hpc/install_hpc_environment.sh
bash hpc/check_hpc_environment.sh
bash hpc/submit_pipeline.sh --phase screening --dry-run
bash hpc/submit_pipeline.sh --phase screening --skip-download
# Review config/candidate_selection.tsv and config/references.tsv first:
bash hpc/submit_pipeline.sh --phase validation
```

All seven wrappers support individual qsub from the project root. afterok dependency generation was tested with mock qsub; actual PBS scheduling was not tested locally. Raw downloads/reference retrieval need a network-enabled node permitted by site policy. Environment prefixes and external database paths must exist on HPC; local compiled environments are not portable artifacts.
