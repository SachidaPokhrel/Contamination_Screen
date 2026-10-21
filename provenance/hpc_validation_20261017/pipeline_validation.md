# Pipeline validation

Executed 2026-10-17T20:45:20.173281+00:00.

| Check | Status | Exit code |
|---|---|---:|
| unit_tests | PASS | 0 |
| Bash/PBS/Python syntax | PASS | 0 |
| Analysis entry point help | PASS | 0 |
| real_mapping | PASS | 0 |
| R_syntax | PASS | 0 |
| offline_demo | PASS | 0 |
| environment_inventory | PASS | 0 |

Offline demo uses explicitly constructed SAM, depth and Kraken report fixtures; it does not validate external alignment, classification or SRA transfer. Mock qsub tests verify dependency arguments and submission handling, not scheduler execution. No actual PBS job was submitted. Unit test logs enumerate individual assertions. Biological results have not been generated.

Logs: logs/tests/. Demo: reports/synthetic_demo/. Missing real-tool checks must be rerun after environment installation.
