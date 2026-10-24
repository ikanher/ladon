#!/usr/bin/env python3
"""Verify frozen report/adjudication, then load the custodian key and aggregate."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ladon._contract_evaluation_core import _loads, canonical_json, read_bytes_bounded
from ladon.contract_evaluation_metrics import aggregate_evaluation, artifact_root_context


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--registration", type=Path, required=True)
    p.add_argument("--first-report", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--adjudication", type=Path, required=True)
    p.add_argument("--key", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    try:
        # Context binding avoids changing the process working directory and applies before
        # registration-linked artifacts are opened by the verifier.
        with artifact_root_context(a.artifact_root):
            registration = _loads(read_bytes_bounded(a.registration, "registration"), "registration")
            receipt = _loads(read_bytes_bounded(a.receipt, "receipt"), "receipt")
            adjudication = _loads(read_bytes_bounded(a.adjudication, "adjudication"), "adjudication")
            report_bytes = read_bytes_bounded(a.first_report, "first report")
            key_path = Path(os.path.abspath(a.key))

            def load_key():
                return read_bytes_bounded(key_path, "key")

            result = aggregate_evaluation(registration, report_bytes, receipt, adjudication, load_key)
        payload = canonical_json(result) + b"\n"
        if len(payload) > 2 * 1024 * 1024:
            raise ValueError("output exceeds limit")
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with a.out.open("xb") as f:
            f.write(payload)
        return 0
    except (ValueError, OSError) as e:
        p.error(str(e))


if __name__ == "__main__":
    raise SystemExit(main())
