# A Pseudomonas screening hit without species-specific validation

**Question.** Does an apparent Pseudomonas sp. CIP-10 detection in two oomycete
readsets survive independent mapping and sequence-specificity checks?

**Data and approach.** Independent DNA WGS (Globisporangium okanoganense CBS315.81,
SRR15309490) and RNA-seq (Phytophthora hibernalis mycelium, SRR16206986) libraries
were screened using 100,000 cleaned paired fragments each. Kraken2 assignments
were treated as hypotheses. Reads were mapped to a representative candidate genome,
with and without the target reference. Primary supporting reads and fragment names,
whole-reference depth and breadth were measured under explicit quality filters.
Reference annotations and selected read-pair nt searches tested specificity.

**Measurements.** Competitive DNA mapping retained 143/200,000 reads (0.0715%),
116 fragments, mean depth0.002899x and breadth>=1x0.017363%. RNA retained128 reads
(0.064%),115 fragments, mean depth0.001705x and breadth>=1x0.021921%. Mean depth
includes uncovered positions across the6,473,352bp reference. RNA support decreased
from266 candidate-only reads to128 after host competition, while genomic rather
than transcriptomic host competition remained a limitation.

**Specificity evidence.** All143 DNA alignments overlapped annotated rRNA on
CP087163.1. Of128 RNA alignments,126 overlapped those rRNA features, one overlapped
a chromosome tRNA-Gln, and one mapped within sucD. Both mates of the sucD pair
matched Phytophthora transcripts. Representative rRNA pairs matched oomycete and
other eukaryotic sequences, often at full-read100% identity. These representative
searches do not establish the origin of every supporting read. Reference labels
alone do not prove plasmid identity, another organism's presence, or database error.

**Assessment supported by the measurements.** The claimed Pseudomonas CIP-10
species assignment was not independently validated. Conserved structural RNA and
alternative homologous matches explain why low-breadth mapping support does not
establish that organism. No biological source or absence claim is established.

**Student decisions to complete.** Significance bin: [Noise / Trace / Consequential /
Biological, with justification]. Likely source: [assignment category or unresolved,
with evidence favouring it over alternatives]. These judgments have deliberately
not been supplied automatically.

**Broader context and limits.** A separate pluspf–Bracken comparison and three
assembly blobplots are included in index.html. Most assembled sequence remains
unclassified and coloured taxa remain hypotheses. For these original readset assembly branches, no completed FCS-GX, independent
viral validation or detection-limit spike-in is reported. Raw readsets are excluded
from the repository; measurements, software specifications and provenance remain.


Additional case: [the independent FCS public-genome analysis](../reports/fcs_analysis.md) documents GCA_051997085.1, selected because the user reports an NCBI contamination flag. It is separate from the original SRA readsets and does not change the measurements above.
