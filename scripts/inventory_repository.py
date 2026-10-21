#!/usr/bin/env python3
"""Record SHA256 for files eligible for publication according to the repository Git rules."""
import argparse
import csv
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Inventory regular files and relative links without hashing excluded runtime products."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    destination = ROOT / 'reports/file_manifest.tsv'
    listing = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT, check=True, capture_output=True).stdout.decode()
    rows = []
    for name in sorted(set(listing.split('\0')) - {''}):
        source = ROOT / name
        if source == destination or not source.exists():
            continue
        if source.is_symlink():
            kind = 'relative_link'
            data = source.readlink().as_posix().encode()
            rows.append(dict(relative_path=name, kind=kind, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        elif source.is_file():
            digest = hashlib.sha256()
            with source.open('rb') as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(block)
            rows.append(dict(relative_path=name, kind='file', bytes=source.stat().st_size, sha256=digest.hexdigest()))
    with destination.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['relative_path', 'kind', 'bytes', 'sha256'], delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    print('Inventoried', len(rows), 'publication files/links; manifest excludes itself.')


if __name__ == '__main__':
    main()
