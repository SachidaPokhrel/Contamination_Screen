#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
INIT="${OOMYCETE_ENV_INIT:-$(python3 "$ROOT/hpc/settings.py" environment_init)}"
if [[ -n "$INIT" ]]; then source "$INIT"; fi
exec "${OOMYCETE_PYTHON:-python3}" -u "$ROOT/hpc/install_environments.py" "$@"
