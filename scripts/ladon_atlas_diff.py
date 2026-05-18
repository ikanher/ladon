#!/usr/bin/env python3
"""Diff two Ladon atlas JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.atlas_diff import diff_atlases, load_atlas, render_atlas_diff_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-json", required=True, help="Earlier atlas JSON path.")
    parser.add_argument("--after-json", required=True, help="Later atlas JSON path.")
    parser.add_argument("--output-json", required=True, help="Path to write diff JSON.")
    parser.add_argument("--output-markdown", help="Optional path to write Markdown diff.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    diff = diff_atlases(load_atlas(Path(args.before_json)), load_atlas(Path(args.after_json)))
    write_json(Path(args.output_json), diff)
    if args.output_markdown:
        Path(args.output_markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_markdown).write_text(render_atlas_diff_markdown(diff), encoding="utf-8")
    return 0


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
