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
import subprocess
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]

for assay, sample in [
    ("DNA", "DNA_Gokan_CBS315_81"),
    ("RNA", "RNA_Phib_mycelia1"),
]:
    mapping = root / "results" / assay / "05_mapping" / sample / "competitive"
    coverage = root / "results" / assay / "06_coverage" / sample / "competitive"
    bam = coverage / "filtered.bam"

    with (mapping / "contigs.tsv").open() as handle:
        contigs = {
            row["contig"]: row["original_contig"]
            for row in csv.DictReader(handle, delimiter="\t")
            if row["reference_id"] == "Pseudomonas_CIP10"
        }

    if not bam.is_file() or not contigs:
        raise SystemExit(f"Missing BAM or candidate contigs: {sample}")

    result = subprocess.run(
        ["samtools", "view", str(bam), *contigs],
        check=True, capture_output=True, text=True,
    )

    sites = Counter()
    fragments = Counter()
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        fragments[fields[0]] += 1
        sites[(contigs[fields[2]], int(fields[3]), fields[5])] += 1

    print(f"\n=== {sample}: competitive mapping ===")
    print(f"Retained reads: {sum(sites.values())}")
    print(f"Distinct supporting fragments: {len(fragments)}")
    print(f"Fragments with two retained alignments: "
          f"{sum(n == 2 for n in fragments.values())}")
    print("original_contig\talignment_start_1based\tCIGAR\tread_count")
    for (contig, position, cigar), count in sites.most_common(15):
        print(contig, position, cigar, count, sep="\t")
