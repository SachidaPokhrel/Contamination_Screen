# scripts

Annotated analysis entry points and implementation modules, report generation, checksum restoration and final-view reconstruction. Main Bash/Python tools support --help. Expensive compute stages require recreated inputs and suitable allocation.

## Contents

| Entry | Type |
|---|---|
| [00_check_environment.sh](00_check_environment.sh) | file |
| [01_download_data.sh](01_download_data.sh) | file |
| [02_read_qc.sh](02_read_qc.sh) | file |
| [03_subsample.sh](03_subsample.sh) | file |
| [04_kraken2_screen.sh](04_kraken2_screen.sh) | file |
| [05_bracken_abundance.sh](05_bracken_abundance.sh) | file |
| [06_select_candidates.py](06_select_candidates.py) | file |
| [07_download_references.sh](07_download_references.sh) | file |
| [08_mapping.sh](08_mapping.sh) | file |
| [09_coverage.sh](09_coverage.sh) | file |
| [10_rna_virus_screen.sh](10_rna_virus_screen.sh) | file |
| [11_detection_table.py](11_detection_table.py) | file |
| [12_visualization.R](12_visualization.R) | file |
| [13_generate_report.py](13_generate_report.py) | file |
| [14_assembly_analysis.sh](14_assembly_analysis.sh) | file |
| [15_rna_assembly.sh](15_rna_assembly.sh) | file |
| [16_dna_denovo.sh](16_dna_denovo.sh) | file |
| [assembly_analysis.py](assembly_analysis.py) | file |
| [assembly_blobplot.R](assembly_blobplot.R) | file |
| [build_report.py](build_report.py) | file |
| [build_test_database.sh](build_test_database.sh) | file |
| [common.py](common.py) | file |
| [dna_denovo.py](dna_denovo.py) | file |
| [dna_denovo_blobplot.R](dna_denovo_blobplot.R) | file |
| [fcs_analysis.py](fcs_analysis.py) | file |
| [inventory_repository.py](inventory_repository.py) | file |
| [make_decision_document.py](make_decision_document.py) | file |
| [pipeline.py](pipeline.py) | file |
| [prepare_database.sh](prepare_database.sh) | file |
| [prepare_final_view.py](prepare_final_view.py) | file |
| [restore_artifacts.py](restore_artifacts.py) | file |
| [review](review/README.md) | directory |
| [rna_assembly.py](rna_assembly.py) | file |
| [rna_blobplot.R](rna_blobplot.R) | file |
| [run_pipeline.sh](run_pipeline.sh) | file |
| [test_database.py](test_database.py) | file |
| [validate_repository.py](validate_repository.py) | file |
| [verify_dataset_metadata.py](verify_dataset_metadata.py) | file |
| [verify_fcs_ncbi.py](verify_fcs_ncbi.py) | file |

[Project overview](../README.md) · [Offline HTML report](../index.html)
