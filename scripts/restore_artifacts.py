#!/usr/bin/env python3
"""Restore retained final FASTA files from verified gzip artifacts, without downloads."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def sha256(file):
    """Stream a checksum so large assemblies do not require additional RAM."""
    digest = hashlib.sha256()
    with file.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    """Validate compressed sources and restore only missing, exact-match assembly outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='Show retained artifacts without restoring')
    args = parser.parse_args()
    entries = json.loads((ROOT / 'metadata/retained_assemblies.json').read_text())
    for entry in entries:
        source, target = ROOT / entry['compressed_path'], ROOT / entry['path']
        if args.list:
            print(entry['compressed_path'], '->', entry['path'])
            continue
        if target.exists():
            if sha256(target) != entry['sha256']:
                raise SystemExit(f'Refusing to replace modified assembly: {target}')
            print('SKIP verified:', entry['path'])
            continue
        if sha256(source) != entry['compressed_sha256']:
            raise SystemExit(f'Compressed artifact checksum mismatch: {source}')
        temporary = target.with_name(target.name + '.restore.partial')
        with gzip.open(source, 'rb') as reader, temporary.open('wb') as writer:
            shutil.copyfileobj(reader, writer)
        if sha256(temporary) != entry['sha256']:
            temporary.unlink()
            raise SystemExit(f'Restored checksum mismatch: {target}')
        temporary.replace(target)
        print('RESTORED:', entry['path'])


if __name__ == '__main__':
    main()
