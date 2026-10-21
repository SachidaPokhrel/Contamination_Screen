#!/usr/bin/env bash
# Resolve the project root before dispatch; quote paths so transfer does not require edits.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ${1:-} == --help ]]; then echo 'Usage: run_stage.sh download|qc|screen|mapping|coverage|viral_analysis|reports [analysis options]'; exit 0; fi
STAGE="${1:?stage required}"; shift
cd "$ROOT"
export PYTHONUNBUFFERED=1
JOB="${PBS_JOBID:-local}"
echo "Stage=$STAGE PBS_JOBID=$JOB root=$ROOT started=$(date -u +%FT%TZ)"
exec_env() { bash "$ROOT/hpc/environment_exec.sh" "$@"; }
case "$STAGE" in
 download) exec_env contamination bash scripts/01_download_data.sh "$@" ;;
 qc) exec_env contamination bash scripts/02_read_qc.sh "$@" ;;
 screen)
  exec_env contamination bash scripts/03_subsample.sh "$@"
  exec_env contamination bash scripts/04_kraken2_screen.sh "$@"
  exec_env contamination bash scripts/05_bracken_abundance.sh "$@"
  exec_env contamination python scripts/06_select_candidates.py "$@" ;;
 mapping)
  exec_env contamination bash scripts/07_download_references.sh "$@"
  exec_env contamination bash scripts/08_mapping.sh "$@" ;;
 coverage) exec_env contamination bash scripts/09_coverage.sh "$@" ;;
 viral_analysis)
  VIRAL="$(python3 -c 'import sys;sys.path.insert(0,"scripts");from common import config;print("viral_analysis" if config()["viral_discovery"] else "contamination")')"
  exec_env "$VIRAL" bash scripts/10_rna_virus_screen.sh "$@" ;;
 reports)
  exec_env contamination python scripts/11_detection_table.py "$@"
  RESULTS="$(python3 -c 'import sys;sys.path.insert(0,"scripts");from common import config,path;print(path(config()["results_dir"]))')"
  exec_env plotting Rscript scripts/12_visualization.R --results "$RESULTS"
  exec_env contamination python scripts/13_generate_report.py "$@" ;;
 *) echo "Unknown PBS stage: $STAGE" >&2; exit 1 ;;
esac
echo "Finished=$STAGE time=$(date -u +%FT%TZ) exit_status=0"
