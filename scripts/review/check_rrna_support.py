#!/usr/bin/env python3
"""Reproduce the targeted specificity review; requires regenerated reads/BAM inputs.

These are historical diagnostic helpers, not new biological validation. Existing
review tables and remote-BLAST outputs are retained for offline inspection.
"""
import sys
if '--help' in sys.argv:
    print(__doc__)
    raise SystemExit(0)
import csv
import re
import subprocess
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]
features = [
    (22, 1039, "16S_rRNA"),
    (1146, 4663, "23S_rRNA"),
    (5499, 5617, "5S_rRNA"),
    (7239, 8012, "partial_16S_rRNA"),
]
rows = []

for assay, sample in [
    ("DNA", "DNA_Gokan_CBS315_81"),
    ("RNA", "RNA_Phib_mycelia1"),
]:
    mapping = root / "results" / assay / "05_mapping" / sample / "competitive"
    bam = root / "results" / assay / "06_coverage" / sample / "competitive" / "filtered.bam"

    with (mapping / "contigs.tsv").open() as handle:
        contigs = {
            r["contig"]: r["original_contig"]
            for r in csv.DictReader(handle, delimiter="\t")
            if r["reference_id"] == "Pseudomonas_CIP10"
        }
    if not bam.is_file() or not contigs:
        raise SystemExit(f"Missing inputs for {sample}")

    result = subprocess.run(
        ["samtools", "view", str(bam), *contigs],
        check=True, capture_output=True, text=True,
    )
    counts = Counter()
    for line in result.stdout.splitlines():
        f = line.split("\t")
        original = contigs[f[2]]
        position = int(f[3])
        blocks = []
        for length, operation in re.findall(r"(\d+)([MIDNSHP=X])", f[5]):
            length = int(length)
            if operation in "M=X":
                blocks.append((position, position + length - 1))
            if operation in "MDN=X":
                position += length

        hits = []
        overlap_bases = 0
        if original == "CP087163.1":
            for start, end, label in features:
                overlap = sum(
                    max(0, min(b, end) - max(a, start) + 1)
                    for a, b in blocks
                )
                if overlap:
                    hits.append(label)
                    overlap_bases += overlap

        category = (
            "annotated_rRNA_overlap" if hits else
            "CP087163.1_outside_annotated_rRNA"
            if original == "CP087163.1" else
            "other_assembly_contig"
        )
        counts[category] += 1
        rows.append({
            "sample_id": sample,
            "read_name": f[0],
            "flag": f[1],
            "original_contig": original,
            "start_1based": f[3],
            "CIGAR": f[5],
            "MAPQ": f[4],
            "category": category,
            "rRNA_features": ";".join(hits),
            "aligned_bases_overlapping_rRNA": overlap_bases,
            "total_aligned_bases": sum(b-a+1 for a, b in blocks),
        })

    print(f"\n=== {sample} ===")
    print("Total retained reads:", sum(counts.values()))
    for category in [
        "annotated_rRNA_overlap",
        "CP087163.1_outside_annotated_rRNA",
        "other_assembly_contig",
    ]:
        print(f"{category}: {counts[category]}")

out = root / "tables/pseudomonas_rrna_alignment_audit.tsv"
out.parent.mkdir(parents=True, exist_ok=True)
fields = [
    "sample_id", "read_name", "flag", "original_contig",
    "start_1based", "CIGAR", "MAPQ", "category", "rRNA_features",
    "aligned_bases_overlapping_rRNA", "total_aligned_bases",
]
with out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
print("\nSaved:", out)
