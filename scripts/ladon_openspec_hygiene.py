#!/usr/bin/env python3
"""Report and optionally normalize OpenSpec status hygiene drift."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ladon.analysis.openspec_hygiene import (
    normalize_completed_active_statuses,
    summarize_openspec_hygiene,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openspec-root", default="openspec", help="OpenSpec root directory.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--check", action="store_true", help="Exit nonzero when drift remains.")
    parser.add_argument(
        "--fix-completed-active",
        action="store_true",
        help="Rewrite active metadata to completed when all tasks are checked.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    openspec_root = Path(args.openspec_root)
    fixed: list[str] = []
    if args.fix_completed_active:
        fixed = normalize_completed_active_statuses(openspec_root)
    summary = summarize_openspec_hygiene(openspec_root)
    payload = {"fixed": fixed, **summary}
    write_payload(payload, Path(args.output_json) if args.output_json else None)
    if args.check and summary["drift_count"] > 0:
        return 1
    return 0


def write_payload(payload: dict, output_json: Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_json is None:
        sys.stdout.write(text)
        return
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
