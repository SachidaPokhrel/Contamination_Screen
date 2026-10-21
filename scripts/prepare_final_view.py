#!/usr/bin/env python3
"""Recreate the portable final-results view from original DNA and round-two RNA evidence."""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Build only relative directory links; refuse to overwrite actual result files."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    for assay, sample in [('DNA', 'DNA_Gokan_CBS315_81'), ('RNA', 'RNA_Phib_mycelia1')]:
        for stage in ['02_kraken2', '03_bracken', '04_candidates', '05_mapping', '06_coverage']:
            base = 'results_round2' if assay == 'RNA' and stage in ['05_mapping', '06_coverage'] else 'results'
            source = ROOT / base / assay / stage / sample
            if not source.is_dir():
                raise SystemExit(f'Missing retained stage: {source}')
            target = ROOT / 'results_final' / assay / stage / sample
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                if target.resolve() != source.resolve():
                    raise SystemExit(f'Existing link points elsewhere: {target}')
            elif target.exists():
                raise SystemExit(f'Refusing to replace existing data: {target}')
            else:
                target.symlink_to(os.path.relpath(source, target.parent), target_is_directory=True)
            print(target.relative_to(ROOT), '->', os.readlink(target))


if __name__ == '__main__':
    main()
