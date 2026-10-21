#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
if [[ ${1:-} == --help ]]; then echo 'Usage: bash hpc/install_dna_spades.sh (creates only optional SPAdes environment)'; exit; fi
if [[ -n "${OOMYCETE_ENV_INIT:-}" ]]; then source "$OOMYCETE_ENV_INIT"; fi
PREFIX="${OOMYCETE_ENV_DIR:-$(python3 hpc/settings.py environment_dir)}"
PREFIX="${PREFIX/#\~/$HOME}"
[[ "$PREFIX" = /* ]] || PREFIX="$ROOT/$PREFIX"
mkdir -p logs/installations
exec > >(tee -a logs/installations/dna_spades.log) 2>&1
trap 'echo "FINISH $(date -Is) status=$?"' EXIT
manager=""
for tool in micromamba mamba conda; do if command -v "$tool" >/dev/null 2>&1; then manager="$tool"; break; fi; done
[[ -n "$manager" ]] || { echo 'Load Conda or Mamba first'; exit 1; }
if [[ ! -d "$PREFIX/rnaspades/conda-meta" ]]; then
 "$manager" env create -p "$PREFIX/rnaspades" -f environments/dna_spades.yml -y
fi
bash hpc/dna_spades_exec.sh spades.py --version
"$manager" list -p "$PREFIX/rnaspades" --explicit > environments/rnaspades_explicit_$(uname -s)_$(uname -m).txt
