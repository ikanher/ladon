#!/usr/bin/env python3
"""Build combined reviewer workflow output from Ladon atlas JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.atlas_workflow import build_atlas_workflow, render_atlas_workflow_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas-json", required=True, help="Current atlas JSON path.")
    parser.add_argument("--before-atlas-json", help="Optional earlier atlas JSON path.")
    parser.add_argument(
        "--bridge-report",
        action="append",
        default=[],
        help="Optional ProofIR bridge report JSON to summarize.",
    )
    parser.add_argument("--output-json", required=True, help="Path to write workflow JSON.")
    parser.add_argument("--output-markdown", help="Optional path to write workflow Markdown.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workflow = build_atlas_workflow(
        load_json(Path(args.atlas_json)),
        before_atlas=load_json(Path(args.before_atlas_json)) if args.before_atlas_json else None,
        bridge_reports=[load_json(Path(path)) for path in args.bridge_report],
    )
    write_json(Path(args.output_json), workflow)
    if args.output_markdown:
        output = Path(args.output_markdown)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_atlas_workflow_markdown(workflow), encoding="utf-8")
    return 0


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
