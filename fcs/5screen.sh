#!/usr/bin/env bash
# Portable replacement for the original cluster-specific screen script.
# Existing files under decontamination/ are retained; new runs use reruns/screen/.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
exec "${FCS_PYTHON:-python3}" -u "$ROOT/scripts/fcs_analysis.py" screen "$@"
