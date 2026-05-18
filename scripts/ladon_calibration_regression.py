#!/usr/bin/env python3
"""Check Ladon report directories against stable calibration predicates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.calibration import evaluate_reports_root, expectation_suites_by_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reports-root",
        default="temp/ladon-live-runs",
        help="Directory containing generated Ladon report JSON files.",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path for machine-readable predicate rows.",
    )
    parser.add_argument(
        "--suite",
        choices=sorted(expectation_suites_by_name()),
        default="live",
        help="Named built-in expectation suite to evaluate.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    suites = expectation_suites_by_name()[args.suite]
    rows = evaluate_reports_root(Path(args.reports_root), suites)
    if args.json_output:
        write_json(Path(args.json_output), rows)
    print_rows(rows)
    return 0 if all(row["passed"] for row in rows) else 1


def print_rows(rows: list[dict]) -> None:
    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{status} {row['report']} {row['predicate']}: {row['message']}")


def write_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
