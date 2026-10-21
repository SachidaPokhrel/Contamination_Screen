# Oomycete contamination: final assessment

Three independent datasets; provisional judgments for student review. These assessments distinguish detection evidence from an unresolved contamination mechanism.

## 1. DNA WGS: Globisporangium okanoganense CBS 315.81

SRR15309490. Pseudomonas CIP-10 competitive mapping retained 143 reads (0.0715% of input reads), mean depth 0.002899x and breadth >=1x 0.01736%. All 143 alignments overlapped rRNA; representative reads also matched oomycete/eukaryotic records. Provisional bin: NOISE for the species assignment. Conserved-sequence cross-mapping is favoured; a bacterial source was not established. This does not prove that every supporting read is host-derived.

## 2. RNA-seq: Phytophthora hibernalis mycelium

SRR16206986. Pseudomonas competitive support was 128 reads (0.0640%), depth 0.001705x and breadth 0.02192%. Of these, 126 overlap rRNA, one tRNA and one sucD; both mates of the sucD pair matched Phytophthora transcripts. Provisional bin: NOISE for Pseudomonas species identification. Miltoncostaea remains noise/unresolved: 11 reads cover only 130 bp with 7–11 mismatches per 90 bp. Conserved-sequence misassignment is more plausible than demonstrated microbial associates.

## 3. FCS-GX public genome: Globisporangium irregulare strain 13-30

GCA_051997085.1; PRJNA816194; SAMN26664723. Selected because the user reports an NCBI contamination flag; exact wording was not independently verified. Supplied completed HPC FCS-GX v0.5.0 output recommends EXCLUDE for 8 complete fungal-labelled contigs: 12,358 bp (0.028973% of assembly bases). Six have top label Cladosporium colombiae; two Melanodothis sp. Provisional bin: CONSEQUENTIAL for assembly curation, because retaining foreign contigs could distort annotation/comparative analysis; an actual downstream effect was not measured. Source: fungal sample/culture carryover suspected, mechanism unresolved. Species labels are provisional. No associated SRA run was verified; read fraction, depth and read-mapping breadth are unavailable.

## Why alternative sources are not favoured

A real associate/cobiont remains possible for the fungal contigs, but presence alone does not establish an association. Integration lacks host–fungal junction evidence. Reagent contamination lacks blanks/batch controls; bleed-through lacks multiplex/index evidence; library chimera lacks a validated chimeric junction. Human screening labels were not independently validated, and no laboratory provenance establishes a lab organism. Database error was not demonstrated: shared conserved sequence can produce ambiguous assignments without erroneous records.

## Scope and evidence

The two readsets used 100,000 cleaned pairs each (200,000 input reads); depth/breadth include uncovered reference positions. Other selected reference negatives do not exclude all strains. Broader human/fungal screening labels and blobplot colours remain hypotheses. FCS assembly-base percentage is not read fraction; exclusion does not prove the retained genome is contamination-free. No independently validated RNA virus or spike-in detection limit is reported. Evidence: tables/detections.tsv; tables/fcs_actions.tsv; reports/fcs_analysis.md; reports/pseudomonas_specificity_review.md; original HPC logs.
