
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

