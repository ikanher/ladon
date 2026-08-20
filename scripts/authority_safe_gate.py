#!/usr/bin/env python3
"""Evaluate two child exit receipts for the authority-safe integration gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.authority_safe_gate import evaluate_authority_safe_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--correctness", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_authority_safe_gate(
        json.loads(args.correctness.read_text(encoding="utf-8")),
        json.loads(args.authority.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
