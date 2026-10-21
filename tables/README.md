# tables

Primary detection evidence, user-editable interpretation columns, alignment-specificity audit, BLAST selections/results and generated QC/screening/Bracken/assembly summaries. Main detection metrics were not altered during curation.

## Contents

| Entry | Type |
|---|---|
| [assembly_summary.tsv](assembly_summary.tsv) | file |
| [assembly_taxonomy_summary.tsv](assembly_taxonomy_summary.tsv) | file |
| [bracken_comparison.tsv](bracken_comparison.tsv) | file |
| [detections.csv](detections.csv) | file |
| [detections.tsv](detections.tsv) | file |
| [fcs_actions.tsv](fcs_actions.tsv) | file |
| [fcs_detections.tsv](fcs_detections.tsv) | file |
| [pseudomonas_alignment_sites.txt](pseudomonas_alignment_sites.txt) | file |
| [pseudomonas_rrna_alignment_audit.tsv](pseudomonas_rrna_alignment_audit.tsv) | file |
| [pseudomonas_rrna_summary.txt](pseudomonas_rrna_summary.txt) | file |
| [qc_summary.tsv](qc_summary.tsv) | file |
| [rrna_specificity_review](rrna_specificity_review/README.md) | directory |
| [screening_summary.tsv](screening_summary.tsv) | file |

## Detection table definitions

`supporting_reads` counts retained primary mate alignments; `supporting_fragments` counts distinct pair names. `read_fraction_percent` uses all200,000 input reads; `fragment_fraction_percent` uses100,000 pairs. `mean_depth` includes zero-coverage reference bases; breadth fields measure >=1x/5x/10x across all contigs. `mapping_mode` separates candidate-only from competitive evidence. `significance_bin`, `likely_source`, `scientific_interpretation` and `evidence_supporting_interpretation` remain user-editable. Bracken estimates have their own modeled-pool denominator and are supplementary.

[Project overview](../README.md) · [Offline HTML report](../index.html)
