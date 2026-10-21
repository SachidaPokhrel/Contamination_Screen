> Historical planning document from the initial implementation. For executed results and current status, see [the project README](../README.md), [methods](10_methods.md) and [HTML report](../index.html).

# Dataset candidates and provisional selection

Eight candidate/lead records are in metadata/dataset_candidates.tsv: four DNA and four RNA. Unknown values are explicit. Three DNA runs have NCBI experiment-to-run metadata; RNA alternatives include one direct NCBI SRA record, two run/BioSample associations verified in a NCBI-hosted primary publication, and one preferred virus-project lead without a resolved run. This is not a claim that every requested metadata field or every RNA run was independently retrieved from SRA.

## Provisional runnable pair
| Assay | Run | Source | Displayed archive size | Rationale |
|---|---|---|---|---|
| DNA | SRR15309490 | Globisporangium okanoganense CBS 315.81 | ~747.6 MB | Paired NextSeq WGS, small run, preferred genus, matched-strain assembly GCA_023334035.1. |
| RNA | SRR16206986 | Phytophthora hibernalis Phibe_mycelia1 | ~817.1 MB | Paired HiSeq RNA-seq, RANDOM selection, modest size and species reference availability. Viral infection is unknown. |

[DNA NCBI experiment](https://www.ncbi.nlm.nih.gov/sra/SRX11614171%5Baccn%5D), [DNA BioProject/assembly associations](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA601986), [RNA NCBI experiment](https://www.ncbi.nlm.nih.gov/sra/SRX12491341), [RNA BioProject/assembly](https://www.ncbi.nlm.nih.gov/bioproject/746351).

NCBI reports 5,888,715 spots for DNA and 6,040,967 for RNA; twice these counts are provisional biological-read expectations for paired runs, to be checked after extraction. Exact per-mate read lengths are not verified and are not inferred from rounded total bases. The RNA assembly GCA_024679025.1 is species-compatible; identity with the RNA isolate has not been established. Original environmental sources and use of prefiltering for the selected runs are not established by retrieved records. Therefore they are cultured-isolate fallbacks, not claimed field metagenomes.

The combined displayed archive estimate is 1.5647 GB, excluding FASTQ, scratch, cleaned reads, environments and databases. config/datasets.tsv deliberately budgets higher archive bounds (0.9 and 1.0 GB) for space checks; these are planning allowances, not exact observed byte counts. The user has approved these two sequencing runs and allow_data_download is true; no sequencing transfer has succeeded because SRA Toolkit is absent and shell DNS fails. Reserve roughly 40 GB conversion space initially using the 20× conservative factor plus retained outputs; refine after NCBI RunInfo/tool size checks.

## Additional dataset used: FCS-GX public genome

| Field | Description |
|---|---|
| Organism / strain | Globisporangium irregulare strain 13-30 |
| Assembly accession | GCA_051997085.1 |
| BioProject | PRJNA816194 |
| BioSample | SAMN26664723 |
| WGS master | JALBZS000000000 |
| NCBI taxonomy ID | 36331 |
| Input | Public assembled genome: 5,451 sequences, 42,653,821 bp |
| Associated SRA run | Not verified; no raw reads from this case were analysed |
| Selection rationale | User selected it because NCBI flagged it as contaminated; exact flag wording was not independently retrieved |
| Analysis performed | Completed HPC FCS-GX screening and cleaning; supplied outputs audited locally |
| Relationship to original datasets | Independent assembly-only case, not the DNA or RNA isolate above |

The [NCBI project assembly table](https://www.ncbi.nlm.nih.gov/bioproject/816194)
links the assembly, strain and BioSample. The supplied FCS action report excludes
eight fungal-labelled contigs totalling 12,358 bp (0.028973% of input assembly).
This percentage measures assembly bases, not reads. Read fraction, depth and
read-mapping breadth are unavailable for this case. The original two readsets
remain the assignment's DNA/RNA pair; this genome is an additional analysis.

See [all analysed datasets](../metadata/analysis_datasets.tsv),
[structured FCS metadata](../metadata/fcs_genome.json) and
[the FCS case report](../reports/fcs_analysis.md). Significance bins and likely
sources remain student decisions.

## Higher-priority leads and alternatives
Globisporangium irregulare CBS 250.28 is verified as [SAMN13878576](https://www.ncbi.nlm.nih.gov/biosample/SAMN13878576), associated with PRJNA601986 and GCA_023336235.1. Its SRA run could not be resolved in accessible records; no neighboring accession was guessed. G. irregulare CBS 494.86 (PRJNA371716) remained a discovery lead at initial selection. PRJNA816194 later supplied the independent FCS public-genome case described above. Switch the provisional DNA selection if exact preferred-species run metadata can be recovered within budget.

The most relevant virus lead is [PRJNA818851](https://www.ncbi.nlm.nih.gov/bioproject/818851). The [primary study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9244493/) reports P. castaneae-associated viruses and paired 101-nt total-RNA sequencing. Importantly, the total RNA library pooled VN999 with P. condilina BD661; pooling constrains source attribution. Run/BioSample linkage for that library is unresolved here. It should be favored for a virus-centered assignment once verified, but its run is not invented or downloaded. Publication-supported viral nucleotide leads are in metadata/viral_reference_candidates.tsv; current versions/taxids must be resolved before retrieval.

Two dual RNA-seq alternatives, SRR9140952 (12 hpi) and SRR9140950 (24 hpi), are linked to PRJNA544637 and their BioSamples in the [NCBI-hosted primary publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7150523/). They use experimentally inoculated coconut leaves rather than field-collected material. Raw-count conventions and archive sizes still require SRA verification; publication “paired end reads” wording is retained without silently converting it to spot counts. Their messenger RNA library preparation constrains virus recovery. They were not selected over the smaller directly verified RNA run.

## Complete verification on a network-enabled machine
```bash
python3 scripts/verify_dataset_metadata.py
python3 scripts/verify_dataset_metadata.py --query 'SAMN13878576[BioSample]'
python3 scripts/verify_dataset_metadata.py --query 'PRJNA818851[BioProject]'
```

These commands retrieve only small metadata records, save raw responses/checksums under metadata/ncbi and never enable downloads. They have not succeeded locally because shell DNS fails. Review exact strategies, library selection, layout, spots, lengths, sizes and reference versions, then update both selected_datasets.tsv and config/datasets.tsv. Choose one run per assay; do not download all runs from a discovery response.
