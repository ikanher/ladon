#!/usr/bin/env python3
"""Reproduce M1 with installed pinned Lean and the current Ladon checkout."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run_demo(output: Path):
    checkout = Path(__file__).resolve().parents[1]
    output.mkdir(parents=True, exist_ok=False)
    repo = output / "repo"
    shutil.copytree(
        checkout / "tests/fixtures/correspondence_m1",
        repo,
        ignore=shutil.ignore_patterns(".ladon", "*.olean"),
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(checkout / "src")
    command = [sys.executable, "-m", "ladon.entrypoint"]
    receipts = []

    def invoke(*args):
        started = time.monotonic()
        process = subprocess.run(
            [*command, *map(str, args)],
            cwd=checkout,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        receipts.append(
            {
                "command": [*command, *map(str, args)],
                "returnCode": process.returncode,
                "elapsedSeconds": time.monotonic() - started,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        )
        (output / "commands.json").write_text(json.dumps(receipts, indent=2) + "\n")
        if process.returncode:
            raise RuntimeError("public command failed: " + process.stdout + process.stderr)

    slice_path = output / "slice.json"
    invoke(
        "proof-search",
        "proof",
        "slice",
        "--repo",
        repo,
        "--source",
        "Proof.lean",
        "--module",
        "Proof",
        "--declaration",
        "Correspondence.term",
        "--application",
        "bridge",
        "--output",
        slice_path,
    )
    for name in ("positive", "false"):
        interpretation, plan, result = [
            output / (name + suffix)
            for suffix in (".interpretation.json", ".plan.json", ".result.json")
        ]
        invoke(
            "investigation",
            "interpret",
            "--record",
            repo / (name + ".json"),
            "--root",
            repo,
            "--slice",
            slice_path,
            "--output",
            interpretation,
        )
        invoke(
            "investigation",
            "align",
            "--interpretation",
            interpretation,
            "--slice",
            slice_path,
            "--map",
            repo / "map.json",
            "--root",
            repo,
            "--output",
            plan,
        )
        invoke(
            "investigation",
            "check",
            "--plan",
            plan,
            "--terms",
            repo / (name + "-terms.json"),
            "--repo",
            repo,
            "--root",
            repo,
            "--output",
            result,
        )
        invoke(
            "investigation",
            "inspect",
            "--plan",
            result,
            "--output",
            output / (name + ".inspection.json"),
        )
        value = json.loads(result.read_text())
        expected = (
            "supported-for-attributed-interpretation"
            if name == "positive"
            else "refuted-correspondence"
        )
        if value["parentSupport"] != expected or value["conditionalValidity"] != "supported":
            raise RuntimeError(name + " did not meet its required real-Lean control outcome")
        if (
            value["interpretationFidelity"] != "attributed-unreviewed"
            or value["methodCorrespondence"] != "unreviewed"
        ):
            raise RuntimeError("checker improperly promoted fidelity or method")
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New directory; never overwrite first receipts"
    )
    args = parser.parse_args()
    run_demo(args.output.resolve())


if __name__ == "__main__":
    main()
