"""Run the bounded native mathematical experiment and existing Ladon consumer."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path
from time import monotonic

import ladon
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--spent-seconds", type=float, default=0)
    args = parser.parse_args()
    if not 0 <= args.spent_seconds < 600:
        parser.error("spent seconds must fit the original 600-second budget")
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent
    toolchain = pinned_toolchain(root)
    library = root / ".lake/build/lib/lean"
    (library / "FeasibilityProbe").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["LEAN_PATH"] = str(library)
    env["PYTHONPATH"] = str(Path(ladon.__file__).resolve().parent.parent)
    lean = str(toolchain.lean_path)
    commands = (
        [
            lean,
            "-o",
            str(library / "FeasibilityProbe/Native.olean"),
            "FeasibilityProbe/Native.lean",
        ],
        [lean, "Acceptance.lean"],
        [lean, "ClosureGuards.lean"],
        [lean, "-o", str(library / "Subjects.olean"), "Subjects.lean"],
        [
            sys.executable,
            "check_completion.py",
            "--output",
            str(output / "completion.json"),
        ],
    )
    sources = (
        "FeasibilityProbe/Native.lean",
        "Acceptance.lean",
        "ClosureGuards.lean",
        "Subjects.lean",
        "check_completion.py",
        "qualify.py",
        "lean-toolchain",
        "lakefile.toml",
    )
    report = {
        "scope": "native mathematical experiment; supplied-term completion, no discovery score",
        "bounds": {"totalSeconds": 600, "maxRssBytes": 12 * 1024**3},
        "priorAttemptSeconds": args.spent_seconds,
        "ladonModule": str(Path(ladon.__file__).resolve()),
        "sources": {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sources
        },
        "processes": [],
        "status": "running",
    }
    started = monotonic()
    for index, command in enumerate(commands):
        remaining = 600 - args.spent_seconds - (monotonic() - started)
        if remaining <= 0:
            raise RuntimeError("parent mathematical probe deadline exhausted")
        result = run_bounded_target_process(
            command,
            cwd=root,
            env=env,
            timeout_seconds=remaining,
            max_output_bytes=8 * 1024**2,
            max_rss_bytes=12 * 1024**3,
            observe_resources=True,
        )
        report["processes"].append(dataclasses.asdict(result))
        report["elapsedSeconds"] = monotonic() - started
        report["status"] = "running" if result.succeeded else "failed"
        (output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(index, result.returncode, round(result.elapsed_seconds, 3), flush=True)
        if not result.succeeded:
            raise RuntimeError(
                "mathematical probe failed; see retained process receipts"
            )
    report["status"] = "passed"
    (output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
