#!/usr/bin/env python3
"""Run the dependency-aware Ladon alpha readiness gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alpha_readiness_plan import build_readiness_plan, load_ledger
from alpha_readiness_run import ReadinessFailure, execute_readiness_plan
from release_gate_candidate import materialize_candidate
from release_gate_runtime import (
    prepare_locked_environment,
    runtime_directory,
    sanitized_environment,
)
from release_gate_types import GateError


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit candidate/readiness command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--ledger",
        required=True,
        help="Dependency ledger path inside the selected candidate.",
    )
    parser.add_argument(
        "--require-all-children",
        action="store_true",
        help="Fail before gates when any resolved child has unchecked tasks.",
    )
    return parser


def project_root() -> Path:
    """Return the live repository containing this script."""

    return Path(__file__).resolve().parents[1]


def ledger_relative_path(raw: str, source_root: Path) -> Path:
    """Resolve a ledger argument and require it to remain inside the source."""

    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (source_root / path).resolve()
    try:
        return resolved.relative_to(source_root.resolve())
    except ValueError as error:
        raise GateError(f"dependency ledger is outside the project: {raw}") from error


def run_readiness(
    *,
    candidate: str,
    ledger: str,
    require_all_children: bool,
) -> dict:
    """Materialize the candidate and execute its dependency-aware gate plan."""

    source_root = project_root()
    ledger_relative = ledger_relative_path(ledger, source_root)
    with materialize_candidate(candidate, source_root) as materialized, runtime_directory(
        "ladon-alpha-readiness-"
    ) as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            prepare_locked_environment(materialized.root, environment)
            payload = load_ledger(materialized.root / ledger_relative)
            plan = build_readiness_plan(materialized.root, payload)
            return execute_readiness_plan(
                plan,
                candidate_root=materialized.root,
                environment=environment,
                require_all_children=require_all_children,
            )


def main(argv: list[str] | None = None) -> int:
    """Run readiness and render one final machine-readable summary."""

    args = build_parser().parse_args(argv)
    try:
        summary = run_readiness(
            candidate=args.candidate,
            ledger=args.ledger,
            require_all_children=args.require_all_children,
        )
    except ReadinessFailure as error:
        print(json.dumps(error.summary, sort_keys=True))
        print(f"alpha readiness: FAIL: {error}", file=sys.stderr)
        return 1
    except GateError as error:
        print(f"alpha readiness: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    print("alpha readiness: PASS", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
