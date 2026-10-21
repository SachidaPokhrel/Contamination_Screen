#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ${1:-} == --help ]]; then echo 'Usage: check_hpc_environment.sh [--config PATH]; checks YAML-created contamination environment and qsub availability'; exit 0; fi
command -v qsub >/dev/null 2>&1 || echo 'WARNING: qsub unavailable here; actual PBS submission cannot be tested' >&2
exec bash "$ROOT/hpc/environment_exec.sh" contamination bash "$ROOT/scripts/00_check_environment.sh" --strict "$@"
