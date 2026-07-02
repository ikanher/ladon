"""Thin CLI for the optional Ladon/ProofIR bridge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from ladon.proofir_bridge import build_bridge_report


def build_parser() -> argparse.ArgumentParser:
    """Return the bridge CLI parser."""

    parser = argparse.ArgumentParser(description="Join a Ladon report with a compact ProofIR bridge index")
    parser.add_argument("--ladon-report", required=True, help="Path to Ladon JSON report")
    parser.add_argument("--proofir-index", help="Path to compact proofir_bridge_index JSON")
    parser.add_argument("--proof-surface-witness", help="Path to optional proof_surface_witness JSON")
    parser.add_argument("--out", required=True, help="Output bridge report JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bridge CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        ladon_report = read_json(Path(args.ladon_report))
        proofir_index = read_json(Path(args.proofir_index)) if args.proofir_index else None
        proof_surface_witness = read_json(Path(args.proof_surface_witness)) if args.proof_surface_witness else None
        report = build_bridge_report(ladon_report, proofir_index, proof_surface_witness=proof_surface_witness)
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"ladon-proofir-bridge: {exc}", file=sys.stderr)
        return 1
    return 0


def read_json(path: Path) -> dict:
    """Read one JSON object from disk."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected JSON object")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
