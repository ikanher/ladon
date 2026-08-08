"""Emit a non-destructive identity and timing baseline for proof-search work."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ladon.proof_search_baselines import (
    baseline_metadata,
    measure_command_phases,
    write_baseline,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--warm-runs", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--probe",
        action="append",
        nargs=argparse.REMAINDER,
        help="argv to measure without shell interpretation; repeat for cold/warm probes",
    )
    args = parser.parse_args(argv)
    probes = args.probe or []
    phases = [
        {
            "argv": probe,
            "phases": measure_command_phases(
                probe, warm_runs=args.warm_runs, timeout=args.timeout
            ),
        }
        for probe in probes
        if probe
    ]
    payload = baseline_metadata(
        args.repo_root,
        command=[sys.executable, *sys.argv],
        measurements=(),
    )
    payload["phaseMeasurements"] = phases
    write_baseline(args.output, payload, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
