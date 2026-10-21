# Software validation

Executed 2026-10-17T20:45:20.173281+00:00. See reports/environment.tsv and logs/tests/environment_inventory.log.

Python and Bash were executed for tests. Local environment installation was attempted and failed because no Conda/Mamba/Micromamba executable was available. Shell DNS probes to NCBI, conda-forge and micromamba failed. No package was installed. YAML constraints were written but not solved, and no environment lockfile is claimed.

FastQC, fastp, SRA Toolkit, Kraken2, Bracken, Bowtie2, minimap2, SAMtools, BLAST+, R, MEGAHIT and DIAMOND execution remains unverified locally unless separately marked PASS above. Actual SRA downloads, database retrieval/build, reference retrieval and HPC scheduling remain untested. The real-mapping check exits 77 when dependencies are missing.
