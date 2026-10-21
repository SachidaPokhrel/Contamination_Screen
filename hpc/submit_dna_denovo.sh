#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
if [[ ${1:-} == --help ]]; then echo 'Usage: bash hpc/submit_dna_denovo.sh [--resume]; submits assemble -> mapping/taxonomy -> BlobToolKit'; exit; fi
[[ $# -eq 0 || ( $# -eq 1 && $1 == --resume ) ]] || { echo 'Unknown arguments' >&2; exit 1; }
[[ -f scripts/assembly_analysis.py && -f hpc/blobtoolkit_exec.sh ]] || { echo 'Apply DNA assembly extension first' >&2; exit 1; }
mkdir -p logs/pbs
submit() {
 local result
 result="$(qsub -o "$ROOT/logs/pbs" "$@")"
 [[ "$result" =~ ^[0-9]+([.][A-Za-z0-9_.-]+)?$ ]] || { echo "Unexpected qsub response: $result" >&2; exit 1; }
 echo "$result"
}
extra=()
if [[ ${1:-} == --resume ]]; then extra=(-v DNA_RESUME=1); fi
assembly="$(submit "${extra[@]}" hpc/pbs/dna_denovo_assemble.pbs)"; echo "assembly=$assembly"
mapping="$(submit -W "depend=afterok:$assembly" hpc/pbs/dna_denovo_mapping.pbs)"; echo "mapping=$mapping"
taxonomy="$(submit -W "depend=afterok:$assembly" hpc/pbs/dna_denovo_taxonomy.pbs)"; echo "taxonomy=$taxonomy"
blob="$(submit -W "depend=afterok:$mapping:$taxonomy" hpc/pbs/dna_denovo_blobtoolkit.pbs)"; echo "blobtoolkit=$blob"
