#!/usr/bin/env python3
"""Write a content-addressed manifest for the pitfall evaluation runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        parser.error("output already exists; frozen manifests are immutable")
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "src/ladon", "pyproject.toml", "uv.lock"],
        check=True, capture_output=True,
    ).stdout.split(b"\0")
    paths = sorted({entry.decode() for entry in tracked if entry})
    files = []
    for name in paths:
        path = root / name
        if path.is_file():
            files.append({"path": name, "state": "present", "sha256": digest(path),
                          "bytes": path.stat().st_size})
        else:
            files.append({"path": name, "state": "missing", "sha256": None, "bytes": None})
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    uv = subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True).stdout.strip()
    payload = {
        "schema": "ladon-pitfall-runtime-freeze-v1",
        "repository": str(root),
        "gitHeadContextOnly": head,
        "python": sys.version,
        "uv": uv,
        "launcher": "openspec/changes/ladon-pitfall-baselines/scripts/ladon-checkout",
        "importRoot": str(root / "src"),
        "trackedFiles": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
