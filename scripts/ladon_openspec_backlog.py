#!/usr/bin/env python3
"""Report OpenSpec backlog and process-hygiene findings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ladon.analysis.openspec_backlog import summarize_openspec_backlog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openspec-root", default="openspec", help="OpenSpec root directory.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--check", action="store_true", help="Exit nonzero when findings are present.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = summarize_openspec_backlog(Path(args.openspec_root))
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        output = Path(args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if args.check and summary["finding_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
