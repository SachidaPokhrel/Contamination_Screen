#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT/tests"
python3 -m unittest test_core.CoreTest.test_subsample_restart_and_stale -v
