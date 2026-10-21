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
from pathlib import Path

sample = "RNA_Phib_mycelia1"
base = Path(__file__).resolve().parents[2] / "results_round2/RNA"

for mode in ("candidate_only", "competitive"):
    mapping = base / "05_mapping" / sample / mode
    bam = base / "06_coverage" / sample / mode / "filtered.bam"

    with (mapping / "contigs.tsv").open() as handle:
        contigs = {
            row["contig"]: row["original_contig"]
            for row in csv.DictReader(handle, delimiter="\t")
            if row["reference_id"] == "Miltoncostaea_pilot"
        }

    if not bam.exists() or not contigs:
        raise SystemExit(f"Missing inputs: {mode}")

    result = subprocess.run(
        ["samtools", "view", str(bam), *contigs],
        check=True, capture_output=True, text=True,
    )
    print(f"\n=== {mode} ===")
    print("read_name\tflag\tcontig\tstart\tMAPQ\tCIGAR\tNM\tAS\tXS")
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        tags = {
            tag.split(":", 2)[0]: tag.split(":", 2)[2]
            for tag in fields[11:]
        }
        print("\t".join([
            fields[0], fields[1], contigs[fields[2]],
            fields[3], fields[4], fields[5],
            tags.get("NM", ""), tags.get("AS", ""), tags.get("XS", ""),
        ]))
