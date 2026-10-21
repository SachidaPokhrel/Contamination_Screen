#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ${1:-} == --help || $# -ne 1 ]]; then echo 'Usage: build_test_database.sh OUTPUT_DIRECTORY; creates a tiny custom synthetic-taxonomy database without network access. Test-only; no real taxonomic inference.'; [[ $# -eq 1 ]] && exit 0 || exit 1; fi
exec python3 -u "$ROOT/scripts/test_database.py" "$1"
