# Fungal-labelled contigs in a previously flagged oomycete genome

**Question.** What does an assembly contamination screen show in public
*Globisporangium irregulare* strain 13-30 genome GCA_051997085.1?
The user selected it because NCBI flagged it as contaminated; the exact current
flag wording was not independently retrieved. This is a known-flagged case,
separate from the original DNA and RNA SRA samples.

**Methods.** Supplied HPC outputs document FCS-GX v0.5.0 with database build
2023-01-24, taxid 36331. The action report and original/clean/excluded FASTAs
were audited locally. No new container run or raw-read analysis was performed.

**Results.** Eight complete contigs, totalling 12,358 bp, receive EXCLUDE actions
in division fung:ascomycetes. Six have top label Cladosporium colombiae
(10,225 bp); two Melanodothis sp. VS III C KN 2 (2,133 bp). The excluded bases
are 0.028973% of the 42,653,821 bp input assembly. Cleaning retains 5,443 of
5,451 sequences and 42,641,463 bp. Sequence/identifier partition checks pass
ignoring case; cleaning removes lowercase soft masking.

**Interpretation limits.** This is evidence of fungal-labelled assembly sequence,
not proof of either named species or its biological source. No read fraction,
sequencing depth or read-mapping breadth is available. FCS alignment coverage
is not read breadth. The NCBI flag and FCS results do not establish a reagent,
associate, integration or database-error mechanism, nor guarantee that all
retained sequence is clean.

**My significance bin:** ______. **My likely source:** ______.
**Evidence favouring my decision over alternatives:** ____________________.
**Remaining uncertainty and next validation:** ____________________.

Assembly metadata: PRJNA816194; SAMN26664723; JALBZS000000000. An associated SRA
run was not verified. Evidence: tables/fcs_actions.tsv; tables/fcs_detections.tsv;
reports/fcs_results.json; fcs/decontamination/; original HPC log in fcs/.
