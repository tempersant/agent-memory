#!/usr/bin/env python3
"""Backward-compatible wrapper — use scripts/handoff.py --to cloud instead."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "handoff.py"


def main() -> int:
    args = ["python3", str(SCRIPT), "--to", "cloud", *sys.argv[1:]]
    return subprocess.call(args)


if __name__ == "__main__":
    raise SystemExit(main())
