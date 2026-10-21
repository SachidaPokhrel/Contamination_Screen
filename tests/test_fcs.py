"""Offline FCS evidence audits and portable-launcher controls, not container screening."""
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fcs_analysis', ROOT / 'scripts/fcs_analysis.py')
fcs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fcs)


class FcsTests(unittest.TestCase):
    def test_supplied_case_partition(self):
        result = fcs.summarize_case(json.loads((ROOT / 'fcs/config.json').read_text()))
        self.assertEqual((result['input_sequences'], result['input_bases']), (5451, 42653821))
        self.assertEqual((result['excluded_sequences'], result['excluded_bases']), (8, 12358))
        self.assertTrue(result['sequence_partition_verified_case_insensitive'])
        self.assertEqual(result['cleaned_lowercase_bases'], 0)
        self.assertEqual(sum(row['flagged_bases'] for row in result['taxa']), 12358)
        self.assertTrue(all(row['read_fraction_percent'] == '' for row in result['taxa']))

    def test_runtime_argument_arrays(self):
        for engine in ['singularity', 'apptainer', 'docker', 'podman']:
            args = fcs.container_prefix(engine, 'local image', [(Path('/tmp/space here'), '/inputs', 'ro')], 2)
            self.assertEqual(args[0], engine)
            self.assertIn('/tmp/space here:/inputs:ro', args)
            if engine in ['docker', 'podman']:
                self.assertIn('--pull=never', args)
        with self.assertRaises(ValueError):
            fcs.container_prefix('docker', 'image', [(Path('/tmp/bad:path'), '/inputs', 'ro')], 2)

    def test_gzip_stdin_and_failure_logging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with gzip.open(root / 'input.fa.gz', 'wt') as stream:
                stream.write('>x\nACGT\n')
            fcs.stream_process([sys.executable, '-c', 'import sys; assert sys.stdin.read()==">x\\nACGT\\n"; print("received")'], root / 'success.log', root / 'input.fa.gz')
            self.assertIn('exit_status=0', (root / 'success.log').read_text())
            with self.assertRaises(RuntimeError):
                fcs.stream_process([sys.executable, '-c', 'raise SystemExit(7)'], root / 'failed.log')
            self.assertIn('exit_status=7', (root / 'failed.log').read_text())

    def test_duplicate_fasta_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.fa'
            path.write_text('>x\nACGT\n>x\nACGT\n')
            with self.assertRaises(ValueError):
                fcs.sequence_records(path)

    def test_inspect_from_another_directory(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/fcs_analysis.py'), 'inspect'], cwd='/tmp', capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('GCA_051997085.1', proc.stdout)

    def test_missing_database_fails_before_run(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/fcs_analysis.py'), 'screen', '--engine', 'docker', '--image', 'local-image', '--db', '/definitely/missing/fcs', '--dry-run'], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('Missing database file', proc.stderr)


if __name__ == '__main__':
    unittest.main()
