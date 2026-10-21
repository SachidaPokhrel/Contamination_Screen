#!/usr/bin/env python3
"""Run offline checks without overwriting historical HPC evidence or biological results."""
import argparse
import ast
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Separate constructed-fixture tests from optional real-software execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-demo', action='store_true', help='Compatibility flag; generated demo copies are no longer retained')
    parser.add_argument('--with-tools', action='store_true', help='Also run the tiny real mapping test if tools are installed')
    args = parser.parse_args()
    logs = ROOT / 'logs/verification'
    reports = ROOT / 'reports/verification'
    logs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    checks = []
    def check(name, command):
        with (logs / f'{name}.log').open('w') as stream:
            result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        status = 'PASS' if result.returncode == 0 else 'SKIP' if result.returncode == 77 else 'FAIL'
        checks.append(dict(check=name, status=status, exit_code=result.returncode))
        print(status, name, flush=True)
    check('unit_and_control_tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v'])
    errors = []
    for base in ['scripts', 'hpc', 'tests']:
        for source in (ROOT / base).rglob('*'):
            if source.suffix in ['.sh', '.pbs']:
                result = subprocess.run(['bash', '-n', str(source)], capture_output=True, text=True)
                if result.returncode:
                    errors.append(str(source.relative_to(ROOT)) + ': ' + result.stderr)
            elif source.suffix == '.py':
                try:
                    ast.parse(source.read_text())
                except SyntaxError as error:
                    errors.append(f'{source.relative_to(ROOT)}: {error}')
    (logs / 'syntax.log').write_text('\n'.join(errors) or 'All Python/Bash/PBS syntax checks passed\n')
    checks.append(dict(check='Python_Bash_PBS_syntax', status='FAIL' if errors else 'PASS', exit_code=int(bool(errors))))
    help_errors = []
    for source in (ROOT / 'scripts').rglob('*'):
        if source.suffix not in ['.py', '.sh'] or source.name == 'common.py':
            continue
        command = ['bash' if source.suffix == '.sh' else sys.executable, str(source), '--help']
        result = subprocess.run(command, cwd='/tmp', capture_output=True, text=True)
        if result.returncode:
            help_errors.append(f'{source.relative_to(ROOT)}: {result.stderr}')
    (logs / 'help.log').write_text('\n'.join(help_errors) or 'All retained Python/Bash analysis entry points support --help\n')
    checks.append(dict(check='independent_entrypoint_help', status='FAIL' if help_errors else 'PASS', exit_code=int(bool(help_errors))))
    if args.with_tools:
        check('real_tiny_mapping', ['bash', 'tests/test_mapping.sh'])
    else:
        checks.append(dict(check='real_bioinformatics_rerun', status='NOT_REQUESTED', exit_code=77))
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (reports / 'test_results.json').write_text(json.dumps(dict(executed_utc=stamp, checks=checks), indent=2) + '\n')
    content = '# Current repository test run\n\nExecuted ' + stamp + '.\n\n| Check | Status | Exit code |\n|---|---|---:|\n'
    content += ''.join(f"| {row['check']} | {row['status']} | {row['exit_code']} |\n" for row in checks)
    content += '\nConstructed fixtures and mocks exercise calculations and control flow. They do not rerun the biological analyses or prove live scheduler execution. Historical HPC validation remains under provenance/hpc_validation_20261017/. Logs are in logs/verification/.\n'
    (reports / 'tests.md').write_text(content)
    raise SystemExit(1 if any(row['status'] == 'FAIL' for row in checks) else 0)


if __name__ == '__main__':
    main()
