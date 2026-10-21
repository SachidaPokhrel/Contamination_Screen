# Repository validation

Checks performed on the curated results copy; no biological analysis was rerun.

- PASS: Every retained directory documented; links resolve; no file >=100 MiB.
- PASS: 16 primary detection rows and exact read-fraction denominators.
- PASS: Both compressed final assemblies match original uncompressed SHA256.
- PASS: FCS original/clean/excluded evidence hashes and audited partition; NCBI flag attribution preserved.
- PASS: Seven real PNGs embedded; all internal report links and anchors resolve.

See [verification/tests.md](verification/tests.md) for the separate synthetic/control test run. Original successful HPC stages are evidenced by their unchanged logs and outputs. A browser rendering test was not available locally; HTML structure, embedded PNG signatures and local targets were checked.
