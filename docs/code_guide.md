# Reading and maintaining the code

## Core read workflow

scripts/common.py owns root-relative path resolution, strict paired FASTQ/FASTA
validation, streamed subprocess logs, tool-specific version commands and locked,
checksum-backed stages. Its function docstrings explain input and counting policies.
Synthetic-test logs are routed separately to logs/verification/synthetic/.

scripts/pipeline.py implements the numbered read stages. Bash/Python entry points
only dispatch to those handlers; they do not duplicate analytical logic. Read
counts are primary alignments and fragment counts are distinct pair names.
coverage() and summarize_depth() include the full reference denominator and do not
exclude uncovered contigs. detection_table() preserves student interpretation
fields by sample/reference/mode/readset key. viral() is optional and was not run;
its presence does not justify a reported detection.

## Assembly branches

assembly_analysis.py assesses the published DNA reference. dna_denovo.py assembles
DNA without reference guidance; rna_assembly.py uses --rna and does not guess
library strandedness. Their stage blocks distinguish assembly, read mapping,
whole-contig taxonomy and BlobToolKit import. SPAdes continuation checks input
content/options before --continue. Assembly mean depth retains mate overlaps;
that differs from the candidate depth policy. classify_rows() computes GC among
ACGT bases, keeps zero-depth contigs, and leaves unknown taxonomy unclassified.
The R companion plots render the same table but are not native viewer exports.

## Report and publication helpers

build_report.py reads final artifacts only: it never invokes assembly, mapping,
classification or a network service. It derives supplementary summary tables,
extracts timestamped log events, and embeds actual PNGs in index.html. It leaves
primary detections.tsv/csv unchanged. restore_artifacts.py decompresses only after
verifying compressed/uncompressed SHA256. prepare_final_view.py reconstructs
relative result links and refuses to overwrite real data. validate_repository.py
checks evidence, embedding, links, file limits and directory documentation.

## Historical specificity scripts

scripts/review/ contains promoted one-off BAM inspections and representative pair
selection. These need regenerated excluded reads/BAMs. Their outputs and BLAST
queries/results remain available for inspection; the helpers support --help and
resolve paths from the project root.

## Tests and changes

The default tests use constructed FASTQ/SAM/depth fixtures and mocked tools; optional
real_mapping tests require installed Bowtie2/SAMtools. reports/verification/ is
separate from archived HPC validation. Stage signatures include Python source
hashes: even documentation/helper additions can invalidate old completion checks.
Never blindly force reruns over retained results; use a new result directory for
new experimental comparisons. No code assigns biological significance or source.
