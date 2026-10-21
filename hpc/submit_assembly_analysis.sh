#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
if [[ ${1:-} == --help ]]; then echo 'Usage: bash hpc/submit_assembly_analysis.sh [--with-fcs]; prepare assembly first. PBS resources may be overridden in wrappers or submit manually.'; exit; fi
[[ $# -eq 0 || ( $# -eq 1 && $1 == --with-fcs ) ]] || { echo 'Unknown arguments' >&2; exit 1; }
[[ -f references/host/Gokan_CBS315_81.fa ]] || { echo 'Run assembly stage first' >&2; exit 1; }
mkdir -p logs/pbs
submit() {
 local result
 result="$(qsub -o "$ROOT/logs/pbs" "$@")"
 [[ "$result" =~ ^[0-9]+([.][A-Za-z0-9_.-]+)?$ ]] || { echo "Unexpected qsub response: $result" >&2; exit 1; }
 echo "$result"
}
mapjob="$(submit hpc/pbs/assembly_mapping.pbs)"; echo "mapping=$mapjob"
taxjob="$(submit hpc/pbs/assembly_taxonomy.pbs)"; echo "taxonomy=$taxjob"
blobjob="$(submit -W "depend=afterok:$mapjob:$taxjob" hpc/pbs/assembly_blobtoolkit.pbs)"; echo "blobtoolkit=$blobjob"
if [[ ${1:-} == --with-fcs ]]; then fcsjob="$(submit hpc/pbs/assembly_fcs.pbs)"; echo "fcs=$fcsjob"; fi
