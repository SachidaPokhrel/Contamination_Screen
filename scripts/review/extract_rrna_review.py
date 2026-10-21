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
import gzip
from pathlib import Path

root = Path(__file__).resolve().parents[2]
audit = root / "tables/pseudomonas_rrna_alignment_audit.tsv"
groups = {}

with audit.open() as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        if row["category"] != "annotated_rRNA_overlap":
            continue
        for feature in row["rRNA_features"].split(";"):
            key = (row["sample_id"], feature)
            groups.setdefault(key, set()).add(row["read_name"])

selected = {}
for (sample, feature), names in sorted(groups.items()):
    name = sorted(names)[0]
    selected.setdefault((sample, name), set()).add(feature)

out = root / "tables/rrna_specificity_review"
out.mkdir(parents=True, exist_ok=True)
records = []
manifest = []

for sample in sorted({s for s, _ in selected}):
    assay = sample.split("_", 1)[0]
    wanted = {name for s, name in selected if s == sample}
    for mate in (1, 2):
        path = root / "data" / assay / "subsampled" / f"{sample}_{mate}.fastq.gz"
        found = set()
        with gzip.open(path, "rt") as handle:
            while True:
                header = handle.readline()
                if not header:
                    break
                sequence = handle.readline().strip()
                plus = handle.readline()
                quality = handle.readline().strip()
                if not plus.startswith("+") or len(sequence) != len(quality):
                    raise SystemExit(f"Invalid FASTQ: {path}")
                name = header.split()[0].removeprefix("@")
                if name.endswith(("/1", "/2")):
                    name = name[:-2]
                if name not in wanted:
                    continue
                if name in found:
                    raise SystemExit(f"Duplicate read ID: {name}")
                found.add(name)
                query = f"{sample}__{name}__mate{mate}"
                records.append(f">{query}\n{sequence}\n")
                manifest.append({
                    "query_id": query,
                    "sample_id": sample,
                    "read_name": name,
                    "mate": mate,
                    "selection_features": ";".join(sorted(selected[(sample, name)])),
                })
        if found != wanted:
            raise SystemExit(f"Missing selected reads in {path}: {wanted-found}")

(out / "representative_pairs.fasta").write_text("".join(records))
with (out / "selection.tsv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=[
        "query_id", "sample_id", "read_name", "mate", "selection_features"
    ], delimiter="\t")
    writer.writeheader()
    writer.writerows(manifest)

print(f"Selected {len(selected)} pairs; wrote {len(records)} sequences.")
print("Output:", out)
