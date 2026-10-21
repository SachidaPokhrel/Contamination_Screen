#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
exec "${OOMYCETE_PYTHON:-python3}" -u scripts/assembly_analysis.py "$@"
