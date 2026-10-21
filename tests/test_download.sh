#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT/tests"
python3 -m unittest test_download_mock test_core.CoreTest.test_pair_errors -v
