#!/usr/bin/env python3
"""Validate registration and freeze an unlabelled first report."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ladon._contract_evaluation_core import _loads, read_bytes_bounded
from ladon.contract_evaluation_metrics import freeze_first_report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--registration", type=Path, required=True)
    p.add_argument("--arm-report", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    try:
        registration = _loads(read_bytes_bounded(a.registration, "registration"), "registration")
        receipt = freeze_first_report(read_bytes_bounded(a.arm_report, "first report"), registration, a.artifact_root, a.receipt)
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0
    except (ValueError, OSError) as e:
        p.error(str(e))

if __name__ == "__main__":
    raise SystemExit(main())
