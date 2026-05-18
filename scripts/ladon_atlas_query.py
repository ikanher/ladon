#!/usr/bin/env python3
"""Run canned queries against a Ladon atlas SQLite database."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ladon.atlas_sqlite import CANNED_QUERIES, run_canned_query


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Atlas SQLite database path.")
    parser.add_argument("--query", required=True, choices=sorted(CANNED_QUERIES))
    parser.add_argument("--output-json", help="Optional JSON output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = run_canned_query(Path(args.db), args.query)
    text = json.dumps(rows, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        output = Path(args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
