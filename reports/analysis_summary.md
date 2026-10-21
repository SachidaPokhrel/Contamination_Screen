# What was run, what was found, and what it means

## 1. Data and quality control

We used DNA WGS from Globisporangium okanoganense CBS315.81 (SRR15309490) and
RNA-seq from Phytophthora hibernalis mycelium (SRR16206986). They are different
species/isolates. SRA retrieval, validation, FastQC and fastp completed on HPC.
DNA retained5,685,476 pairs; RNA retained5,941,455 pairs. Raw reads are not bundled.

## 2. Screening and independent reference measurements

Seeded subsamples of100,000 pairs per dataset were screened with Kraken2. These
were hypotheses rather than proven contaminants. Manually chosen references
were assessed with candidate-only and host-competitive mapping, MAPQ20 filtering,
read/fragment counts and zero-inclusive whole-reference depth/breadth.

- Pseudomonas CIP-10: competitive DNA143 reads/116 fragments,0.0715% of input
  reads, mean depth0.002899x, breadth>=1x0.017363%. RNA128 reads/115 fragments,
  0.064%, depth0.001705x, breadth0.021921%. Very little of the reference is covered.
- Acetobacteroides and Tateyamaria: zero retained support against the selected
  representative references in both datasets. This does not exclude every strain.
- Stenotrophomonas: zero retained RNA support against its chosen representative.
- Miltoncostaea:11 competitive RNA reads/11 fragments,0.0055%, mean depth0.000218x,
  breadth0.002862%, concentrated in one130bp interval. Species identity remains
  unresolved; the optional follow-up interval BLAST was skipped.

## 3. Why Pseudomonas was not independently validated

All143 DNA alignments overlapped annotated rRNA on CP087163.1. RNA had126 rRNA
alignments, one tRNA-Gln overlap and one sucD alignment. Both mates of the sucD
pair matched Phytophthora transcripts. Representative rRNA pairs also had strong
matches to oomycete and other eukaryotic records. These observations undermine
species specificity; they do not prove every read is host-derived or establish a
database error. Full evidence: pseudomonas_specificity_review.md.

## 4. Separate Kraken2–Bracken comparison

A second screening used the pluspf database and matching Bracken distributions
(150bp DNA;100bp RNA as an approximation to predominantly90bp reads). Estimates
included Bremia, human and fungal labels. Bracken reallocates classification
support; it does not confirm organism identity or provide depth/breadth.
Its model fraction is not the fraction of all100,000 input pairs. See
../tables/bracken_comparison.tsv for both denominators. These estimates remain
separate from the original mapping measurements.

## 5. Assemblies and blobplots

Three completed branches have native BlobToolKit datasets and R-rendered figures:

| Branch | Sequences | Total bases | N50 |
|---|---:|---:|---:|
| Published same-isolate DNA genome |5,631|44,209,726|15,859bp|
| De novo SPAdes DNA, full cleaned reads |18,388|46,890,401|17,970bp|
| De novo rnaSPAdes RNA, full cleaned reads |27,606|26,496,841|1,750bp|

Full cleaned reads were mapped to the relevant assembly, and Kraken2 assigned
whole-contig labels. Most sequence remained unclassified (99.997%,99.754% and
99.646% of bases, respectively). Coloured human/microbial contigs are candidates
for further validation, not automatically real contamination. RNA coverage also
reflects expression and isoform mapping ambiguity. N50 is descriptive, not proof
of completeness or accuracy. All three blobplots are embedded in ../index.html.

## 6. What was not established

For the original readset assembly branches, no completed FCS-GX report was supplied; submissions encountered a site hook error.
No independent viral protein search/viral validation or spike-in detection-limit
experiment was completed. RNA assembly is not equivalent to finding a virus.
Human/fungal and other screening labels were not all independently validated.

## 7. Decisions remaining with the student

Choose and defend noise/trace/consequential/biological bins and likely sources.
Use the evidence and explicitly acknowledge unresolved alternatives. Do not infer
harmlessness from a low fraction, organism presence from a high MAPQ alone, or a
specific contamination source from a Kraken label. The primary detection table
keeps user-editable columns, and final_decisions.docx is a compact decision worksheet.
For metric definitions and evidence needed for each source, see interpretation_guide.md.


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
