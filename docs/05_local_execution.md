> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# Local execution

Local inspection found WSL2/Ubuntu x86_64, 12 logical CPUs, 3.7 GiB RAM and about 941 GiB free project storage. Use 2 threads for local tests. /tmp is a 1.9 GiB tmpfs, so fasterq-dump uses configurable work/tmp instead. Recheck resources with scripts/00_check_environment.sh. Network access through the shell currently fails DNS; package installation and biological downloads cannot run until resolved outside this restricted execution environment.

Use a manager already installed on Linux/WSL, not a Windows Conda binary. Set OOMYCETE_ENV_INIT to an initialization script if needed; set OOMYCETE_ENV_DIR to an external directory writable by your account. The default is ~/.local/share/oomycete-envs. Run hpc/install_hpc_environment.sh; --update explicitly applies changed YAML, and --with-viral enables the optional assembly/search environment. Installation verifies executables and writes environment_versions.tsv plus platform-specific explicit exports on success. The YAML combination has not been solved locally.

To execute with proper environments:
```bash
bash hpc/environment_exec.sh contamination bash scripts/00_check_environment.sh --strict
bash tests/test_pipeline.sh
bash hpc/environment_exec.sh contamination bash tests/test_mapping.sh
```

See docs/08_output_explanation.md for each stage. All analysis Bash/Python entry points accept --config, --sample and --help. --force explicitly rebuilds a stale stage; inspect the log first. --pairs changes only subsampling; mapping/classification use config readset (raw, cleaned or subsampled). Do not compare full-read mapping numerators to subsample denominators.

The default orchestrator runs download through candidates and then stops for manual review. Reference retrieval and mapping require selected rows in candidate_selection.tsv. To run validation only, use --from-stage references --to-stage table. Plotting can use the separate plotting environment. Specialized assembly is disabled unless viral_discovery=true and a prepared, documented DIAMOND protein database path is supplied; install --with-viral and run stage 10 in viral_analysis.

A tiny custom Kraken test database can be built without network, once Kraken2 is installed:
```bash
bash hpc/environment_exec.sh contamination bash scripts/build_test_database.sh work/test_kraken_db
```
It contains artificial sequences and taxonomy and is unsuitable for biological detection. Broad external Kraken2 databases generally exceed this laptop's RAM. Test subsampling does not reduce database memory needs. Memory mapping can trade memory pressure for slower disk access and does not guarantee a broad database fits.

To move data externally, set data_dir and scratch_dir in config. Absolute external paths are intentionally machine-specific and must be reset on HPC; relative paths transfer automatically. Input files supplied via raw_r1/raw_r2 take precedence for raw reads. Completion manifests contain checksums, code/config signatures and portable project-relative paths. Transfer those manifests with outputs to retain verified skips.
