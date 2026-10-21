#!/usr/bin/env bash
# Clean explicitly using the new screen report or --action-report PATH.
# Input is streamed/decompressed; original FASTAs and reports are never replaced.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
exec "${FCS_PYTHON:-python3}" -u "$ROOT/scripts/fcs_analysis.py" clean "$@"
