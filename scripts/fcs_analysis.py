#!/usr/bin/env python3
"""Portable Linux FCS-GX screening/cleaning and offline audit of the supplied public-genome case.

No PBS, module command, Conda environment, downloaded fcs.py, or cluster path is
required. Supply an existing local container and database. No automatic downloads
or replacement of historical outputs occur. Summarization needs only Python.
"""
import argparse
from collections import Counter, defaultdict
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]


def resolve(value):
    """Resolve configured relative paths against this repository, never the caller's cwd."""
    source = Path(os.path.expandvars(os.path.expanduser(str(value))))
    return source if source.is_absolute() else ROOT / source


def sha256(source):
    digest = hashlib.sha256()
    with Path(source).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def sequence_records(source):
    """Read plain/gzip DNA FASTA and reject malformed or duplicate identifiers."""
    opener = gzip.open if str(source).endswith('.gz') else open
    records, name, chunks = {}, None, []
    with opener(source, 'rt') as stream:
        for line in stream:
            if line.startswith('>'):
                if name is not None:
                    if not chunks:
                        raise ValueError('Empty FASTA sequence: ' + name)
                    records[name] = ''.join(chunks)
                name = line[1:].split()[0]
                if name in records:
                    raise ValueError('Duplicate FASTA identifier: ' + name)
                chunks = []
            elif line.strip():
                if name is None or not re.fullmatch('[ACGTURYSWKMBDHVNacgturyswkmbdhvn]+', line.strip()):
                    raise ValueError('Invalid nucleotide FASTA: ' + str(source))
                chunks.append(line.strip())
    if name is None or not chunks:
        raise ValueError('Empty FASTA: ' + str(source))
    records[name] = ''.join(chunks)
    return records


def action_records(source):
    """Parse an NCBI action report; keep the report version/database metadata separately."""
    metadata, lines = {}, []
    with Path(source).open() as stream:
        for line in stream:
            if line.startswith('##[['):
                metadata = json.loads(line[2:])[1]
            elif line.startswith('#seq_id'):
                lines.append(line[1:])
            elif line.strip() and not line.startswith('#'):
                lines.append(line)
    if not lines:
        raise ValueError('Missing FCS action report header: ' + str(source))
    rows = list(csv.DictReader(lines, delimiter='\t'))
    for row in rows:
        for key in ['start_pos', 'end_pos', 'seq_len']:
            row[key] = int(row[key])
        if not 1 <= row['start_pos'] <= row['end_pos'] <= row['seq_len']:
            raise ValueError('Invalid FCS interval: ' + row['seq_id'])
    return metadata, rows


def summarize_case(config):
    """Verify original/clean/excluded sequence partition and summarize only measured assembly evidence."""
    input_path = resolve(config['input_fasta'])
    clean_path = resolve(config['recorded_clean_fasta'])
    excluded_path = resolve(config['recorded_contaminant_fasta'])
    action_path = resolve(config['recorded_action_report'])
    original, clean, excluded = (sequence_records(source) for source in [input_path, clean_path, excluded_path])
    metadata, actions = action_records(action_path)
    # This supplied case contains full-contig EXCLUDE actions; do not generalize
    # this partition audit to interval masking/splitting without additional logic.
    full_excludes = all(row['action'] == 'EXCLUDE' and row['start_pos'] == 1 and row['end_pos'] == row['seq_len'] for row in actions)
    partition = False
    normalized_matches = False
    if full_excludes:
        ids = {row['seq_id'] for row in actions}
        partition = set(excluded) == ids and set(clean).isdisjoint(excluded) and set(clean) | set(excluded) == set(original)
        normalized_matches = partition and all(original[key].upper() == value.upper() for key, value in {**clean, **excluded}.items())
        if not partition or not normalized_matches:
            raise ValueError('Supplied original/clean/excluded FASTA partition does not match the action report')
        for row in actions:
            if len(original[row['seq_id']]) != row['seq_len']:
                raise ValueError('Action report length differs from input FASTA')
    input_bases, clean_bases, excluded_bases = (sum(map(len, records.values())) for records in [original, clean, excluded])
    by_taxon = defaultdict(list)
    for row in actions:
        by_taxon[row['top_tax_name']].append(row)
    taxa = []
    for name, rows in sorted(by_taxon.items()):
        bases = sum(row['end_pos'] - row['start_pos'] + 1 for row in rows)
        taxa.append(dict(assembly_accession='GCA_051997085.1', top_tax_name=name, sequences=len({row['seq_id'] for row in rows}), flagged_bases=bases, input_assembly_bases_percent=100 * bases / input_bases, significance_bin='', likely_source='', read_fraction_percent='', mean_depth='', read_mapping_breadth_percent='', evidence='FCS-GX action report, not independent read-mapping validation'))
    return dict(assembly_accession='GCA_051997085.1', taxid=config['taxid'], input_sequences=len(original), input_bases=input_bases, cleaned_sequences=len(clean), cleaned_bases=clean_bases, excluded_sequences=len(excluded), excluded_bases=excluded_bases, excluded_assembly_percent=100 * excluded_bases / input_bases, actions=actions, taxa=taxa, fcs_metadata=metadata, exact_id_partition_verified=partition, sequence_partition_verified_case_insensitive=normalized_matches, retained_sequences_with_case_changes=sum(original[key] != value for key, value in clean.items()), input_lowercase_bases=sum(sum(ch.islower() for ch in seq) for seq in original.values()), cleaned_lowercase_bases=sum(sum(ch.islower() for ch in seq) for seq in clean.values()), file_sha256={str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source):sha256(source) for source in [input_path, clean_path, excluded_path, action_path]}, scope='Independent public assembly only; read fraction, depth and read-mapping breadth are unavailable.')


def write_summaries(config):
    """Publish derived tables/JSON without modifying the supplied action or taxonomy reports."""
    summary = summarize_case(config)
    target = ROOT / 'reports/fcs_results.json'
    target.write_text(json.dumps(summary, indent=2) + '\n')
    for name, rows in [('fcs_actions.tsv', summary['actions']), ('fcs_detections.tsv', summary['taxa'])]:
        with (ROOT / 'tables' / name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter='\t')
            writer.writeheader()
            writer.writerows(rows)
    return summary


def container_prefix(engine, image, binds, threads):
    """Construct argument arrays for local runtimes; paths with spaces remain single arguments."""
    for source, destination, mode in binds:
        if any(ch in str(source) for ch in [':', ',', '\n']):
            raise ValueError('Container mount paths must not contain colon, comma or newline')
    if engine in ['apptainer', 'singularity']:
        args = [engine, 'exec', '--cleanenv', '--env', f'GX_NUM_CORES={threads}']
        for source, destination, mode in binds:
            args += ['--bind', f'{source}:{destination}:{mode}']
        return args + [str(image)]
    if engine in ['docker', 'podman']:
        args = [engine, 'run', '--rm', '-i', '--pull=never', '--cpus', str(threads), '--env', f'GX_NUM_CORES={threads}', '--user', f'{os.getuid()}:{os.getgid()}']
        for source, destination, mode in binds:
            args += ['--volume', f'{source}:{destination}:{mode}']
        return args + [str(image)]
    raise ValueError('Unsupported container engine: ' + engine)


def build_command(stage, config, action_report=None):
    """Build a screen or clean command against a fresh output directory, without PBS."""
    engine = config['engine']
    image = resolve(config['image']) if engine in ['apptainer', 'singularity'] else config['image']
    fasta = resolve(config['input_fasta']).resolve()
    output = resolve(config['output_dir']).resolve() / stage
    binds = [(fasta.parent, '/inputs', 'ro'), (output, '/outputs', 'rw')]
    if stage == 'screen':
        database = resolve(config['database']).resolve()
        binds.append((database, '/db', 'ro'))
        inside = ['python3', '/app/bin/run_gx', '--fasta', '/inputs/' + fasta.name, '--out-dir', '/outputs', '--gx-db', '/db/all.gxi', '--tax-id', str(config['taxid'])]
    else:
        action_report = Path(action_report).resolve()
        binds.append((action_report.parent, '/reports', 'ro'))
        inside = ['/app/bin/gx', 'clean-genome', '--action-report', '/reports/' + action_report.name, '--output', '/outputs/clean.fasta', '--contam-fasta-out', '/outputs/contaminated.fasta']
    return container_prefix(engine, image, binds, config['threads']) + inside, output


def stream_process(command, log_path, input_fasta=None):
    """Stream merged tool output to the console/log and decompress FASTA into clean-genome stdin."""
    with log_path.open('a', buffering=1) as log:
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        header = f'START {stamp}\nCOMMAND {shlex.join(command)}\n'
        print(header, end='', flush=True)
        log.write(header)
        process = subprocess.Popen(command, stdin=subprocess.PIPE if input_fasta else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False)
        errors = []
        def feed():
            try:
                opener = gzip.open if str(input_fasta).endswith('.gz') else open
                with opener(input_fasta, 'rb') as source:
                    shutil.copyfileobj(source, process.stdin)
            except Exception as error:
                errors.append(error)
            finally:
                process.stdin.close()
        writer = threading.Thread(target=feed) if input_fasta else None
        if writer:
            writer.start()
        for line in iter(process.stdout.readline, b''):
            text = line.decode(errors='replace')
            sys.stdout.write(text)
            sys.stdout.flush()
            log.write(text)
        code = process.wait()
        if writer:
            writer.join()
        footer = f'FINISH {dt.datetime.now(dt.timezone.utc).isoformat()} exit_status={code}\n'
        print(footer, end='', flush=True)
        log.write(footer)
        if code or errors:
            raise RuntimeError(f'FCS container failed: exit={code}; stdin_errors={errors}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['inspect', 'screen', 'clean', 'summarize'])
    parser.add_argument('--config', default='fcs/config.json')
    parser.add_argument('--engine', choices=['auto', 'apptainer', 'singularity', 'docker', 'podman'])
    parser.add_argument('--image', help='Local SIF path or already-present Docker/Podman image; no image is downloaded')
    parser.add_argument('--db', help='Directory containing all.gxi and companion database files')
    parser.add_argument('--fasta', help='Plain or gzip FASTA')
    parser.add_argument('--taxid', type=int)
    parser.add_argument('--threads', type=int)
    parser.add_argument('--output-dir', help='Separate rerun output root; historical outputs are protected')
    parser.add_argument('--action-report', help='Explicit report for cleaning; otherwise use a unique newly screened report')
    parser.add_argument('--dry-run', action='store_true', help='Validate paths and print a command without running the container')
    args = parser.parse_args()
    config = json.loads(resolve(args.config).read_text())
    overrides = {'engine': args.engine or os.environ.get('FCS_ENGINE'), 'image': args.image or os.environ.get('FCS_IMAGE'), 'database': args.db or os.environ.get('FCS_DB'), 'input_fasta': args.fasta, 'taxid': args.taxid, 'threads': args.threads, 'output_dir': args.output_dir}
    config.update({key:value for key,value in overrides.items() if value is not None})
    if config.get('schema_version') != 1 or int(config['threads']) < 1 or int(config['taxid']) < 1:
        raise ValueError('Invalid configuration schema, threads or taxonomy ID')
    if args.stage == 'summarize':
        summary = write_summaries(config)
        print(f"Verified {summary['excluded_sequences']} excluded contigs / {summary['excluded_bases']:,} bases ({summary['excluded_assembly_percent']:.6f}% of assembly)")
        return
    if config['engine'] == 'auto':
        config['engine'] = next((engine for engine in ['apptainer', 'singularity', 'docker', 'podman'] if shutil.which(engine)), 'unavailable')
    if args.stage == 'inspect':
        print(json.dumps(config, indent=2))
        for engine in ['apptainer', 'singularity', 'docker', 'podman']:
            print(engine, shutil.which(engine))
        print('RAM estimate GiB:', round(os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE') / 1024**3, 1))
        print('Large-memory execution is recommended for performance; no fixed cluster resource request is imposed.')
        return
    if not config['image']:
        raise ValueError('Set --image or FCS_IMAGE to an existing container; no download is automatic')
    if config['engine'] not in ['apptainer', 'singularity', 'docker', 'podman']:
        raise ValueError('Install/load a container runtime or specify --engine for a dry run')
    if not args.dry_run and not shutil.which(config['engine']):
        raise ValueError('Container engine not available: ' + config['engine'])
    if config['engine'] in ['apptainer', 'singularity'] and not resolve(config['image']).is_file():
        raise FileNotFoundError('Container image missing: ' + config['image'])
    source = resolve(config['input_fasta'])
    if not source.is_file():
        raise FileNotFoundError('Input FASTA missing: ' + str(source))
    if args.stage == 'screen':
        if not config['database']:
            raise ValueError('Set --db or FCS_DB; the database is not downloaded automatically')
        for name in ['all.gxi', 'all.gxs', 'all.taxa.tsv']:
            if not (resolve(config['database']) / name).is_file():
                raise FileNotFoundError('Missing database file: ' + name)
        action = None
    else:
        candidates = [resolve(args.action_report)] if args.action_report else list((resolve(config['output_dir']) / 'screen').glob('*.fcs_gx_report.txt'))
        if len(candidates) != 1 or not candidates[0].is_file():
            raise ValueError('Choose one valid --action-report or complete a new screen first')
        action = candidates[0]
    command, output = build_command(args.stage, config, action)
    if output.is_relative_to(ROOT / 'fcs/decontamination'):
        raise ValueError('Historical FCS reports cannot be used as a rerun output directory')
    if args.dry_run:
        print(shlex.join(command))
        return
    output.mkdir(parents=True, exist_ok=True)
    lock = output.parent / (args.stage + '.lock')
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    try:
        nonempty = [source for source in output.iterdir() if source.name != 'README.md']
        if nonempty:
            raise ValueError('Output directory already has data; choose a new --output-dir instead of overwriting a completed or interrupted run')
        log = output.parent / (args.stage + '.log')
        stream_process(command, log, source if args.stage == 'clean' else None)
        products = (list(output.glob('*.fcs_gx_report.txt')) + list(output.glob('*.taxonomy.rpt'))) if args.stage == 'screen' else [output / 'clean.fasta', output / 'contaminated.fasta']
        if args.stage == 'screen' and (not list(output.glob('*.fcs_gx_report.txt')) or not list(output.glob('*.taxonomy.rpt'))):
            raise RuntimeError('Screen requires both an action report and a taxonomy report')
        if not products or not all(product.is_file() for product in products):
            raise RuntimeError('Container returned success but required output is missing')
        identity = dict(config=config, command=command, input_sha256=sha256(resolve(config['input_fasta'])), output_sha256={str(product):sha256(product) for product in products})
        if config['engine'] in ['apptainer', 'singularity']:
            identity['container_image_sha256'] = sha256(resolve(config['image']))
        if args.stage == 'screen':
            identity['database_inventory'] = [{'name': entry.name, 'bytes': entry.stat().st_size, 'mtime_ns': entry.stat().st_mtime_ns} for entry in sorted(resolve(config['database']).glob('all.*')) if entry.is_file()]
        if action:
            identity['action_report_sha256'] = sha256(action)
        (output.parent / (args.stage + '_manifest.json')).write_text(json.dumps(identity, indent=2) + '\n')
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'ERROR {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(1)
