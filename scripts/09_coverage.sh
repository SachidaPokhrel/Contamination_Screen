#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec "${OOMYCETE_PYTHON:-python3}" -u "$SCRIPT_DIR/pipeline.py" coverage "$@"
