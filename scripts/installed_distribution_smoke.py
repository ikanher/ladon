#!/usr/bin/env python3
"""Build and smoke an explicitly selected Ladon distribution candidate."""

from __future__ import annotations

import argparse
from pathlib import Path

from release_gate_candidate import materialize_candidate
from release_gate_distribution import (
    build_distributions,
    run_installed_distribution_checks,
)
from release_gate_runtime import (
    assert_lock_unchanged,
    assert_no_absolute_maintainer_paths,
    lock_digest,
    runtime_directory,
    sanitized_environment,
)
from release_gate_types import GateError


def build_parser() -> argparse.ArgumentParser:
    """Build the required explicit-candidate interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, materialized directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--package-resource",
        action="append",
        default=[],
        help="Require package:relative/path through archives and installed package.",
    )
    return parser


def project_root() -> Path:
    """Return the repository containing this script."""

    return Path(__file__).resolve().parents[1]


def run_smoke(candidate: str, resources: list[str]) -> None:
    """Build, install, and smoke one selected source candidate."""

    with materialize_candidate(candidate, project_root()) as materialized:
        with runtime_directory("ladon-installed-smoke-") as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            expected_lock = lock_digest(materialized.root)
            assert_no_absolute_maintainer_paths(materialized.root)
            artifacts = build_distributions(
                materialized.root,
                runtime_root,
                environment,
            )
            run_installed_distribution_checks(
                materialized.root,
                artifacts,
                runtime_root,
                environment,
                resources,
            )
            assert_lock_unchanged(materialized.root, expected_lock)
    print("installed distribution smoke: PASS")


def main(argv: list[str] | None = None) -> int:
    """Run the smoke and render deterministic failures."""

    args = build_parser().parse_args(argv)
    try:
        run_smoke(args.candidate, args.package_resource)
    except GateError as error:
        print(f"installed distribution smoke: FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
