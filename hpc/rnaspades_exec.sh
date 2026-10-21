#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ${1:-} == --help ]]; then echo 'Usage: environment_exec.sh rnaspades COMMAND [ARGS...]'; exit 0; fi
ENVIRONMENT="rnaspades"
case "$ENVIRONMENT" in rnaspades) ;; *) echo 'Unknown environment' >&2; exit 1;; esac
INIT="${OOMYCETE_ENV_INIT:-}"
if [[ -z "$INIT" ]]; then INIT="$(python3 "$ROOT/hpc/settings.py" environment_init)"; fi
if [[ -n "$INIT" ]]; then source "$INIT"; fi
PREFIX="${OOMYCETE_ENV_DIR:-$(python3 "$ROOT/hpc/settings.py" environment_dir)}"
PREFIX="${PREFIX/#\~/$HOME}"
[[ "$PREFIX" = /* ]] || PREFIX="$ROOT/$PREFIX"
for manager in micromamba mamba conda; do
 if command -v "$manager" >/dev/null 2>&1; then
  [[ -d "$PREFIX/$ENVIRONMENT/conda-meta" ]] || { echo "Environment missing: $PREFIX/$ENVIRONMENT; run hpc/install_hpc_environment.sh" >&2; exit 1; }
  MANAGER_PATH="$(type -P "$manager" || true)"
  if [[ -z "$MANAGER_PATH" && "$manager" == conda ]]; then MANAGER_PATH="${CONDA_EXE:-}"; fi
  [[ -n "$MANAGER_PATH" ]] || { echo "Cannot resolve executable for $manager" >&2; exit 1; }
  # Quote the entire child command so older Conda preparsers cannot consume child flags.
  printf -v COMMAND '%q ' "$@"
  if [[ "$manager" == conda ]]; then exec "$MANAGER_PATH" run --no-capture-output -p "$PREFIX/$ENVIRONMENT" bash -c "exec $COMMAND"; fi
  exec "$MANAGER_PATH" run -p "$PREFIX/$ENVIRONMENT" bash -c "exec $COMMAND"
 fi
done
echo 'No Conda/Mamba manager found. Load the cluster module or set OOMYCETE_ENV_INIT to its initialization script.' >&2
exit 1
