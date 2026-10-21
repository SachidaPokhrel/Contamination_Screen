#!/usr/bin/env python3
"""Run report; all implementation and --help are in pipeline.py."""
import sys
from pipeline import main
if __name__ == "__main__":
    raise SystemExit(main(["report"] + sys.argv[1:]))
