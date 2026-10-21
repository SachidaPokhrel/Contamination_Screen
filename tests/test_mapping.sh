#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ${1:-} == --help ]]; then echo 'Usage: test_mapping.sh; runs real Bowtie2/SAMtools synthetic mapping if installed, otherwise exits 77'; exit 0; fi
for t in bowtie2 bowtie2-build samtools; do command -v "$t" >/dev/null || { echo "SKIP real mapping: missing $t"; exit 77; }; done
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
python3 "$ROOT/tests/make_fixture.py" "$WORK"
bash "$ROOT/scripts/08_mapping.sh" --config "$WORK/config.yaml"
bash "$ROOT/scripts/09_coverage.sh" --config "$WORK/config.yaml"
python3 - "$ROOT" "$WORK" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'scripts'))
from common import table
w=Path(sys.argv[2]);expected=json.loads((w/'expected.json').read_text())
for mode in ['candidate_only','competitive']:
 rows=table(w/'results/DNA/06_coverage/SYNTHETIC_DNA'/mode/'coverage.tsv');r=next(x for x in rows if x['reference_id']=='fixture')
 for key,value in expected.items():assert abs(float(r[key])-value)<1e-6,(mode,key,r[key],value)
print('PASS real Bowtie2/SAMtools candidate-only and competitive alignment plus coverage')
PY
