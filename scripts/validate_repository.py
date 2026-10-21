#!/usr/bin/env python3
"""Validate curated result integrity, embedded report images, relative links and GitHub limits."""
import argparse
import ast
import base64
import csv
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class ReportParser(HTMLParser):
    """Collect report links and image content without executing JavaScript or fetching URLs."""
    def __init__(self):
        super().__init__()
        self.links, self.images, self.ids = [], [], set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'img':
            self.images.append(attrs.get('src', ''))


def main():
    """Fail clearly on missing evidence, invalid compression, broken links or oversized publication files."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    errors, checks = [], []
    for source in ROOT.rglob('*'):
        if '.git' in source.parts or '__pycache__' in source.parts:
            continue
        if source.is_symlink():
            if not source.exists():
                errors.append(f'Broken relative link: {source.relative_to(ROOT)}')
            continue
        if source.is_dir() and not (source / 'README.md').is_file():
            # Test logs and caches are transient, ignored runtime products.
            if not source.is_relative_to(ROOT / 'logs/verification'):
                errors.append(f'Missing directory README: {source.relative_to(ROOT)}')
        if source.is_file():
            if source.stat().st_size >= 100 * 1024 ** 2:
                errors.append(f'GitHub oversized file: {source.relative_to(ROOT)}')
            if source.suffix == '.py':
                ast.parse(source.read_text())
    checks.append('Every retained directory documented; links resolve; no file >=100 MiB')
    with (ROOT / 'tables/detections.tsv').open() as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    if len(rows) != 16:
        errors.append(f'Unexpected primary detection row count: {len(rows)}')
    for row in rows:
        expected = 100 * int(row['supporting_reads']) / int(row['input_reads'])
        if abs(float(row['read_fraction_percent']) - expected) > 1e-10:
            errors.append('Read fraction denominator mismatch: ' + row['reference_id'])
    checks.append('16 primary detection rows and exact read-fraction denominators')
    for entry in json.loads((ROOT / 'metadata/retained_assemblies.json').read_text()):
        source = ROOT / entry['compressed_path']
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry['compressed_sha256']:
            errors.append('Compressed assembly hash mismatch: ' + entry['compressed_path'])
        digest = hashlib.sha256()
        with gzip.open(source, 'rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != entry['sha256']:
            errors.append('Restored assembly hash mismatch: ' + entry['compressed_path'])
    checks.append('Both compressed final assemblies match original uncompressed SHA256')
    fcs = json.loads((ROOT / 'reports/fcs_results.json').read_text())
    if not fcs['exact_id_partition_verified'] or not fcs['sequence_partition_verified_case_insensitive'] or fcs['excluded_bases'] != 12358:
        errors.append('FCS summary partition/count mismatch')
    for relative, expected in fcs['file_sha256'].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            errors.append('FCS primary evidence hash mismatch: ' + relative)
    metadata = json.loads((ROOT / 'metadata/fcs_genome.json').read_text())
    if metadata['ncbi_contamination_flag']['reported_by'] != 'user':
        errors.append('NCBI contamination flag attribution lost')
    checks.append('FCS original/clean/excluded evidence hashes and audited partition; NCBI flag attribution preserved')
    parser = ReportParser()
    parser.feed((ROOT / 'index.html').read_text())
    if len(parser.images) != 7:
        errors.append(f'Expected seven embedded figures, found {len(parser.images)}')
    for image in parser.images:
        if not image.startswith('data:image/png;base64,'):
            errors.append('Report image depends on an external file or URL')
        elif not base64.b64decode(image.split(',', 1)[1], validate=True).startswith(b'\x89PNG\r\n\x1a\n'):
            errors.append('Invalid embedded PNG')
    for link in parser.links:
        parts = urlsplit(link)
        if parts.scheme or parts.netloc:
            continue
        if not parts.path:
            if parts.fragment and parts.fragment not in parser.ids:
                errors.append('Broken report section anchor: ' + link)
        elif not (ROOT / unquote(parts.path)).exists():
            errors.append('Broken report evidence link: ' + link)
    checks.append('Seven real PNGs embedded; all internal report links and anchors resolve')
    report = '# Repository validation\n\nChecks performed on the curated results copy; no biological analysis was rerun.\n\n'
    report += ''.join(f'- PASS: {check}.\n' for check in checks if not errors)
    if errors:
        report += '\n' + '\n'.join('- FAIL: ' + error for error in errors) + '\n'
    report += '\nSee [verification/tests.md](verification/tests.md) for the separate synthetic/control test run. Original successful HPC stages are evidenced by their unchanged logs and outputs. A browser rendering test was not available locally; HTML structure, embedded PNG signatures and local targets were checked.\n'
    (ROOT / 'reports/repository_validation.md').write_text(report)
    for check in checks:
        print(('CHECK' if errors else 'PASS'), check)
    if errors:
        raise SystemExit('\n'.join(errors))


if __name__ == '__main__':
    main()
