# How to interpret this analysis

## What each measurement signifies

| Measurement | Meaning | What it does not establish |
|---|---|---|
| Kraken assignment | Sequence similarity to taxonomic content in that database | True species identity, contamination or source |
| Bracken estimate | Model-based redistribution of Kraken support | Independent confirmation; per-reference depth or breadth |
| Supporting reads | Retained primary alignments of individual mate sequences | Independent original DNA/RNA molecules |
| Supporting fragments | Distinct read-pair names with either mate supporting a reference | Distinct molecules after deduplication, or proof both mates support the reference |
| Read fraction | Supporting reads divided by all input reads, times100 | Fraction of cells, biomass, or necessarily physical DNA mass |
| Mean depth | Sum of aligned coverage divided by the complete reference length, including zeros | Uniform genomic support; values depend on RNA expression and filtering |
| Breadth at1x | Percent of reference bases covered at least once | Species specificity; conserved genes can generate breadth |
| Breadth at5x/10x | Percent covered at least5/10 times | Independent molecule support; repeats and duplicates can inflate local depth |
| MAPQ | Mapper confidence within its search/reference set | Taxonomic uniqueness against all organisms; a high value cannot rescue a misleading reference set |
| N50 | Half the assembled bases lie in sequences at least this long | Correctness, completeness or freedom from contamination |

Candidate mapping used200,000 reads/100,000 pairs per assay. For example,128
supporting reads means0.064% of all input reads. Breadth0.021921% means only about
0.022% of that reference was covered, not2.2%. Read and fragment fractions differ.
Assembly coverage and candidate coverage used different mate-overlap policies;
keep their definitions separate when comparing values.

## What a blobplot signifies

- X-axis:GC fraction; groups of sequences can differ in composition.
- Y-axis:mean retained read depth+0.001, on a log scale; zero-depth sequences are
  shown at the offset rather than discarded.
- Point area:contig/transcript length.
- Colour:provisional Kraken whole-contig label; it is not a validated organism.

A distinct GC/depth group is a reason to investigate. It could also be organellar,
repetitive, low-expression, misassembled, or otherwise genuine target sequence.
RNA depth depends on expression and isoforms; it is not directly comparable to
DNA copy number. Unclassified sequence is not automatically host or contamination.

## The four significance bins

| Bin | Question to answer | Evidence needed |
|---|---|---|
| Noise | Is the claimed detection credible at its stated taxonomic resolution? | Examine alignment specificity, quality, coverage distribution and better alternative matches; a low count alone is insufficient |
| Trace | Is a small amount of real non-target sequence supported, with no material effect on the intended analysis? | First establish identity, then justify the limited impact; low abundance alone cannot establish harmlessness |
| Consequential | Would retaining this sequence change assembly, gene prediction, expression or another intended analysis? | Show or argue a concrete analytical effect, even if overall abundance is low |
| Biological | Is a credible association/infection/co-occurring organism interesting in its own right? | Require taxonomic specificity, coherent genomic/transcript evidence and context beyond an isolated conserved hit |

These bins are evidence judgments, not fixed read-fraction cutoffs. Significance
and source are separate decisions. The assignment leaves them to the student.

## Evidence for likely source, and alternatives to consider

| Possible source | Evidence that would favour it | Limitation in this project |
|---|---|---|
| Real associate/cobiont | Specific support across multiple loci, coherent contigs, biological context and replication | Selected conserved-locus matches do not establish an associate |
| Integrated into host genome | Host–foreign junctions supported by spanning reads and consistent placement/coverage | A foreign match or contig by itself does not establish integration |
| Reagent | Same taxon in extraction/library blanks or a batch pattern tied to reagents | No such control evidence is established here |
| Bleed-through | Matching co-sequenced source library/index evidence, usually weak recipient support | Low counts alone cannot distinguish it from other sources |
| Library chimera | Independent reads support an artificial junction inconsistent with authentic sequence | A discordant pair alone is insufficient |
| Human | Human-specific multi-locus sequence support with competing taxa excluded | A Homo sapiens label does not independently validate human sequence or its route of entry |
| Lab organism | Specific identification plus connection to handled lab strains/materials | Organism names alone do not supply laboratory provenance |
| Database error | Demonstrable wrong-reference sequence/taxonomy, supported by independent comparisons | Shared rRNA and alternate hits do not by themselves prove database error |

If the available evidence cannot distinguish sources, say so rather than inventing
one. Keep screening-only labels distinct from independently evaluated detections.

## What your current results support

- Pseudomonas CIP-10:species-specific support was not demonstrated. Structural RNA
  dominates support and alternate oomycete matches exist. Final significance/source
  still require your stated reasoning; exact read origins are unresolved.
- Acetobacteroides, Tateyamaria and the selected Stenotrophomonas reference:no
  retained mapping support under these choices/filters, not proof of universal absence.
- Miltoncostaea:localized imperfect support over130bp; species identity/source unresolved.
- Human/Bremia/fungal labels in abundance or contig results:screening candidates,
  not independently confirmed contaminants or associates.
- RNA transcripts and blobplots:completed analysis products, not independent viral
  validation. No completed FCS-GX result is reported for the original readset assembly branches; the separate public-genome FCS case is documented below. No spike-in experiment was performed.


## Added public-genome FCS-GX case (2026-10-20)

The separate *Globisporangium irregulare* strain 13-30 assembly GCA_051997085.1
(PRJNA816194; SAMN26664723) was selected because **the user reports NCBI flagged
it as contaminated**; exact flag wording was not independently retrieved.
Supplied completed FCS-GX outputs recommend excluding eight fungal-labelled
contigs: 12,358 bp, 0.028973% of assembly bases. This is independent of the
original two SRA readsets; no SRA run or raw-read metrics were verified for this
additional case. Student bins/sources remain unassigned. See the
[FCS case report](../reports/fcs_analysis.md) and
[portable Linux instructions](../docs/15_fcs_linux.md).
