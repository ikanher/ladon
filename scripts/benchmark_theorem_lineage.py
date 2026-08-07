"""Record observational theorem-lineage timings without committing databases."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from ladon.proof_search_index import inspect_proof_search_index
from ladon.theorem_cli import theorem_main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--theorem", required=True)
    parser.add_argument("--index")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    status = inspect_proof_search_index(root, index_path=Path(args.index) if args.index else None)
    samples = []
    for _ in range(max(1, args.repetitions)):
        started = time.monotonic()
        exit_code = theorem_main(["lineage", args.theorem, "--repo-root", str(root), "--refresh", "never", "--format", "json", "--output", "-"])
        samples.append({"elapsedSeconds": round(time.monotonic() - started, 6), "exit": exit_code})
    payload = {"schema": "ladon-theorem-lineage-benchmark-v1", "repository": str(root), "theorem": args.theorem, "index": status, "samples": samples, "observational": True}
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
