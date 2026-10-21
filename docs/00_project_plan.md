> Historical planning document from the initial implementation. For executed results and current status, see [the project README](../README.md), [methods](10_methods.md) and [HTML report](../index.html).

# Project plan — approval draft

Status: Plan approved by the user on 2026-10-17. Implementation and offline tests proceeded. Environment installation could not proceed without a manager/network; the user has now approved the two provisional sequencing runs and data downloads are enabled, but missing tools/network prevent retrieval. See reports/pipeline_validation.md for executed checks and limits.

## Scope and deliverables
Build a portable, restartable Bash/Python/R repository for one DNA WGS run and one RNA-seq run. Produce objective classification, alignment, coverage and abundance evidence; leave significance and source judgments blank for the student. Full SRA runs are downloaded only after run-level verification and explicit size approval. A local synthetic test is independent of biological datasets and large databases.

## Phases and gates
1. Inspect system and write planning documents (current phase).
2. Verify at least three DNA and three RNA candidates where available against NCBI run, BioSample and BioProject records; choose exactly one run per assay, documenting unresolved metadata explicitly.
3. Create version-constrained Conda YAML definitions and an idempotent installer; install only after approval and network availability. Record resolved versions and platform-specific exports.
4. Implement all independently runnable stages, shared configuration/logging helpers, PBS wrappers and documentation. Never represent skeletons as finished stages.
5. Obtain approval of exact selected runs and byte estimates before full downloads; references and databases require explicit enabled configuration. Never download an entire BioProject implicitly.
6. Run deterministic synthetic end-to-end validation, followed by 100,000-pair biological screening where resources allow. Distinguish mock tests, real-tool tests and biological runs in reports.
7. Validate PBS syntax and dependency submission with a mock qsub; actual scheduler validation requires the target cluster.
8. Package provenance, checksums, editable tables, plots, methods and transfer instructions.

## Analytical stages
See 04_pipeline_design.md for inputs, outputs, command templates and dependencies; see 03_resource_estimates.md for provisional costs. Main sequence: download → QC → paired subsample → Kraken2 → optional Bracken → candidate review → reference retrieval → mapping → coverage → viral validation → tables/plots/report. Candidate review is an explicit checkpoint: absence of selected candidates must produce actionable instructions, never invented selections.

## Completion criteria
Every requested script exists with working --help and input validation; tests assert known outcomes including multi-contig zero coverage; portable paths survive relocation; execution reports distinguish passed, failed and unavailable checks. Full biological analysis is not claimed until executed. Local environments and large databases are excluded from the portable package.
