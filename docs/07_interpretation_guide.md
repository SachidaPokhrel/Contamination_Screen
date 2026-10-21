# Interpreting detection evidence

Kraken2 generates hypotheses. Evaluate reference compatibility, full-length breadth, depth distribution, primary-read MAPQ, agreement across mates and competitive alignment before assigning biological meaning. High counts restricted to rRNA, repeats, conserved domains or one short contaminated reference region may be misleading. Closely related taxa can exchange assignments; MAPQ is aligner/database-dependent and is not a probability that an organism truly occurred in the sample. MAPQ 255 denotes unavailable quality and is excluded.

Read fraction measures sequencing representation, not cell fraction or biomass. The denominator includes all reads in the same input readset. A fragment can support two different references if its mates map differently; do not sum per-reference fragment fractions as disjoint totals. Primary reads are counted once per alignment, but PCR duplicates are excluded only if previously flagged; this pipeline does not mark duplicates. Compare depth both with and without duplicate exclusion when scientifically warranted. Mean depth and breadth aggregate full reference lengths, including zero contigs; a long reference can obscure a localized signal.

RNA depth depends on expression and transcript structure. Low genomic breadth is not automatically weak RNA evidence; near-complete viral-genome coverage is useful but still requires sequence-specific support. Bowtie2 is not splice-aware: genomic host competition can underestimate host alignment. Prefer an explicit transcriptome or an independently justified splice-aware validation analysis. Candidate-only support can overestimate specificity; inspect the competitive result and alternative related references. A zero viral table can mean no viral reference was selected, not absence of viruses. Viral protein homology alone is also insufficient: examine RdRp motifs, ORFs, coverage, sequence composition and nonviral homologs. Host subtraction can erase integrated/shared viral regions, so it is not applied silently.

## Student significance decisions
| Bin | Evidence to consider before assigning |
|---|---|
| Noise | Weak, nonunique, localized or unreproducible signal consistent with technical/background explanations. |
| Trace | Low-level but independently supported sequence presence; quantify limits and uncertainty. |
| Consequential | Supported signal sufficient to affect assembly, quantification or assignment conclusions. |
| Biological | Evidence consistent with a real organism/association in the biological material, with technical alternatives assessed. |

No universal read-count or breadth cutoff separates these bins. Document the assignment's definition and your reasoning rather than treating configurable screening thresholds as significance rules.

## Source hypotheses and discriminating evidence
| Source | Useful evidence; missing controls limit conclusions |
|---|---|
| Real associate/cobiont | Broad specific coverage, independent samples or assays, ecological plausibility and controls. |
| Integrated into host genome | Host–candidate junction reads, host-depth continuity and long contiguous linkage; RNA detection alone cannot establish integration. |
| Reagent contamination | Extraction blanks, batch association, low-input enrichment and reagent histories. |
| Sequencing bleed-through | Shared run/index context, characteristic low relative signal and a plausible high-abundance donor. |
| Library chimera | Reproducible split/discordant read junctions, library-method context and inspection of alignment artifacts. |
| Human | Specific human sequences with adequate competitive references and handling context. |
| Laboratory organism | Laboratory inventory/context and specific reference-supported reads; common labels alone are insufficient. |
| Database error | Detections confined to a mislabeled/foreign reference contig and contradictory sequence similarity/provenance. |

Keep significance_bin, likely_source, scientific_interpretation and evidence_supporting_interpretation blank until reviewed. Original controls are not provided by the pipeline and no conclusion should imply they exist. For every chosen source, state alternatives and the next experiment needed.
