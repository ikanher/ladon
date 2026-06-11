#!/usr/bin/env python3
"""Export a compact atlas from a directory of Ladon report JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.atlas import build_report_atlas, render_atlas_markdown, render_reviewer_cards_markdown
from ladon.atlas_sqlite import write_atlas_sqlite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reports-root",
        required=True,
        help="Directory containing generated Ladon report JSON files.",
    )
    parser.add_argument("--output-json", required=True, help="Path to write atlas JSON.")
    parser.add_argument("--output-markdown", help="Optional path to write atlas Markdown.")
    parser.add_argument("--output-sqlite", help="Optional path to write derived atlas SQLite.")
    parser.add_argument("--output-cards", help="Optional path to write reviewer-card Markdown.")
    parser.add_argument(
        "--bridge-report",
        action="append",
        default=[],
        help="Optional ProofIR bridge report JSON to summarize in reviewer cards.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    atlas = build_report_atlas(Path(args.reports_root))
    bridge_reports = load_json_files(args.bridge_report)
    write_json(Path(args.output_json), atlas)
    if args.output_markdown:
        write_markdown(Path(args.output_markdown), atlas)
    if args.output_sqlite:
        write_atlas_sqlite(atlas, Path(args.output_sqlite), bridge_reports=bridge_reports)
    if args.output_cards:
        write_cards(Path(args.output_cards), atlas, bridge_reports)
    return 0


def write_json(path: Path, atlas: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, atlas: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_atlas_markdown(atlas), encoding="utf-8")


def write_cards(path: Path, atlas: dict, bridge_reports: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_reviewer_cards_markdown(atlas, bridge_reports), encoding="utf-8")


def load_json_files(paths: list[str]) -> list[dict]:
    return [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]


if __name__ == "__main__":
    raise SystemExit(main())
