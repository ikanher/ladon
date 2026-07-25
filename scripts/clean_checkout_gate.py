#!/usr/bin/env python3
"""Verify a tracked Ladon candidate in a sanitized outside-checkout workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from release_gate_candidate import collection_comparison_root, materialize_candidate
from release_gate_distribution import (
    assert_installed_resource,
    assert_resource_in_artifacts,
    build_distributions,
    install_wheel,
    run_installed_distribution_checks,
)
from release_gate_runtime import (
    assert_collection_parity,
    assert_lock_unchanged,
    assert_no_absolute_maintainer_paths,
    collect_candidate_node_ids,
    collect_live_node_ids,
    prepare_locked_environment,
    run_candidate_quality,
    runtime_directory,
    sanitized_environment,
)
from release_gate_types import GateError


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit-candidate command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, materialized directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Stop after tracked-input, quality, lock, and constrained-build checks.",
    )
    parser.add_argument(
        "--package-resource",
        action="append",
        default=[],
        help="Require package:relative/path in sdist, wheel, and isolated install.",
    )
    return parser


def project_root() -> Path:
    """Return the live repository containing this script."""

    return Path(__file__).resolve().parents[1]


def run_gate(candidate: str, baseline_only: bool, resources: list[str]) -> None:
    """Run the clean candidate's fail-fast verification sequence."""

    source_root = project_root()
    with materialize_candidate(candidate, source_root) as materialized:
        with runtime_directory("ladon-clean-gate-") as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            expected_lock = prepare_locked_environment(
                materialized.root,
                environment,
            )
            assert_no_absolute_maintainer_paths(materialized.root)
            assert_selected_collection_parity(
                candidate,
                source_root,
                materialized.kind,
                materialized.root,
                environment,
            )
            run_candidate_quality(materialized.root, environment)
            artifacts = build_distributions(
                materialized.root,
                runtime_root,
                environment,
            )
            if baseline_only:
                verify_requested_resources(
                    resources,
                    artifacts,
                    runtime_root,
                    environment,
                )
            else:
                run_installed_distribution_checks(
                    materialized.root,
                    artifacts,
                    runtime_root,
                    environment,
                    resources,
                )
            assert_lock_unchanged(materialized.root, expected_lock)
    print("clean checkout gate: PASS")


def assert_selected_collection_parity(
    candidate: str,
    source_root: Path,
    candidate_kind: str,
    materialized_root: Path,
    environment,
) -> None:
    """Check collection against only the source selected by the candidate mode."""

    candidate_nodes = collect_candidate_node_ids(materialized_root, environment)
    comparison_root = collection_comparison_root(
        candidate,
        source_root,
        candidate_kind,
    )
    if comparison_root is None:
        return
    source_nodes = collect_live_node_ids(comparison_root)
    assert_collection_parity(source_nodes, candidate_nodes)


def verify_requested_resources(
    resources: list[str],
    artifacts,
    runtime_root: Path,
    environment,
) -> None:
    """Verify requested resources even in baseline-only mode."""

    if not resources:
        return
    for resource in resources:
        assert_resource_in_artifacts(resource, artifacts)
    installed = install_wheel(artifacts, runtime_root, environment)
    for resource in resources:
        assert_installed_resource(installed, resource, runtime_root, environment)


def main(argv: list[str] | None = None) -> int:
    """Run the gate and render deterministic failures."""

    args = build_parser().parse_args(argv)
    try:
        run_gate(args.candidate, args.baseline_only, args.package_resource)
    except GateError as error:
        print(f"clean checkout gate: FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
