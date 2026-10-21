> Historical planning document from the initial implementation. For executed results and current status, see [the project README](../README.md), [methods](10_methods.md) and [HTML report](../index.html).

# Software requirements and inspection

Inspection date: 2026-10-17. Platform: Ubuntu 26.04.1 LTS, x86_64, Linux kernel 6.18.33.2-microsoft-standard-WSL2. This is WSL2 on Windows; Linux Bash scripts can run directly inside this environment. GNU Bash 5.3.9, Python 3.14.4 and Git 2.53.0 are available.

Not found on PATH: Conda, Mamba, Micromamba, R, prefetch, fasterq-dump, vdb-validate, FastQC, fastp, seqkit, Kraken2, Bracken, Bowtie2, minimap2, SAMtools, BLAST+, pigz and qsub. These are PATH observations, not an exhaustive filesystem inventory. No software has been installed.

## Proposed environments
Use conda-forge and bioconda with strict channel priority. Main environment: Python 3.11, SRA Toolkit 3.x, FastQC 0.12.x, fastp 0.24.x, seqkit 2.x, Kraken2 2.1.x, Bracken 3.x, Bowtie2 2.5.x, minimap2 2.x, SAMtools 1.x, BLAST+ 2.x, pigz, pandas and PyYAML. Plotting environment: R 4.x, ggplot2, readr and dplyr. Optional viral environment: MEGAHIT 1.2.x and DIAMOND 2.x; activate only when assembly discovery is requested. Exact compatible patch versions must be resolved and recorded during installation; these are proposed version ranges, not verified solver results.

The requested main YAML will include R/plotting dependencies; a separate plotting YAML permits independent cluster deployment. Optional environments are not installed by default. Environment prefixes are configurable and external to the transfer package; YAML files must recreate environments on the target Linux system. Do not copy compiled local environments to HPC.

## Scientific tool justifications
| Tool | Justification |
|---|---|
| SRA Toolkit | Retrieves archived runs, validates SRA containers and converts them to paired FASTQ. |
| FastQC | Summarizes sequence quality, adapters and composition before and after cleaning. |
| fastp | Performs paired read cleaning with auditable JSON and HTML reports. |
| seqkit | Provides sequence inspection and deterministic sequence sampling utilities. |
| Kraken2 | Provides rapid taxonomic screening as a hypothesis generation step. |
| Bracken | Re-estimates taxonomic abundance using database-specific read-length models. |
| Bowtie2 | Aligns short Illumina reads to candidate and competitive reference sets. |
| minimap2 | Supplies an optional alternative for divergent or longer reference-supported alignment. |
| SAMtools | Sorts, indexes, filters and summarizes alignments and per-base coverage. |
| BLAST+ | Checks candidate sequence similarity against explicitly chosen reference collections. |
| pigz | Compresses FASTQ streams using configurable parallelism. |
| Python/pandas/PyYAML | Validates configuration and aggregates reproducible tabular evidence. |
| R/ggplot2/readr/dplyr | Produces publication-quality coverage and abundance visualizations. |
| MEGAHIT (optional) | Assembles RNA-derived reads for exploratory viral contig recovery when reference mapping is insufficient. |
| DIAMOND (optional) | Detects protein-level viral similarity in translated assembled contigs. |
| Git | Tracks scripts, configurations and documentation independently of large biological inputs. |

Local HTTPS probes to NCBI and conda-forge failed with temporary DNS resolution errors. NCBI pages were reachable through the browsing service; that does not establish shell download connectivity. Recheck before installation. No network security settings were changed.
