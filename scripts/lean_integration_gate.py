#!/usr/bin/env python3
"""Run required real-Lean extraction through an installed candidate wheel."""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Iterator, Mapping
from pathlib import Path

from release_gate_candidate import materialize_candidate
from release_gate_distribution import (
    assert_installed_import_origin,
    build_distributions,
    executable_path,
    install_wheel,
)
from release_gate_runtime import (
    assert_lock_unchanged,
    assert_no_absolute_maintainer_paths,
    lock_digest,
    run_checked,
    runtime_directory,
    sanitized_environment,
)
from release_gate_types import GateError


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit candidate and mandatory-mode interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, materialized directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Treat an unavailable reference Lean toolchain as a gate failure.",
    )
    return parser


def project_root() -> Path:
    """Return the repository containing this script."""

    return Path(__file__).resolve().parents[1]


def resolve_lake(environment: Mapping[str, str]) -> str | None:
    """Return the Lake executable selected by the sanitized PATH."""

    return shutil.which("lake", path=environment.get("PATH"))


def reference_version(
    lake: str,
    fixture: Path,
    environment: Mapping[str, str],
) -> str:
    """Print and return the fixture-selected Lean/Lake version."""

    result = run_checked(
        [lake, "--version"],
        cwd=fixture,
        environment=environment,
        capture_output=True,
    )
    version = result.stdout.strip()
    print(f"reference toolchain: {version}")
    expected = fixture.joinpath("lean-toolchain").read_text(encoding="utf-8").strip()
    expected_version = expected.rsplit(":v", maxsplit=1)[-1]
    if expected_version not in version:
        raise GateError(
            f"fixture selected unexpected Lean version: expected {expected_version}, got {version}"
        )
    return version


def json_strings(value: object) -> Iterator[str]:
    """Yield every string nested in JSON-like report data."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from json_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from json_strings(nested)


def assert_declaration_evidence(report: Path) -> None:
    """Require the pinned fixture declaration in installed Lean output."""

    payload = json.loads(report.read_text(encoding="utf-8"))
    expected = "LadonFixture.fixtureIdentity"
    if expected not in set(json_strings(payload)):
        raise GateError(f"Lean report omits expected declaration evidence: {expected}")


def run_real_lean(
    candidate_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> None:
    """Build/install the wheel and run explicit-build Lean extraction."""

    fixture = candidate_root / "tests" / "fixtures" / "lean_integration"
    lake = resolve_lake(environment)
    if lake is None:
        raise GateError("required executable is unavailable: lake")
    reference_version(lake, fixture, environment)
    artifacts = build_distributions(candidate_root, runtime_root, environment)
    installed = install_wheel(artifacts, runtime_root, environment)
    assert_installed_import_origin(installed, runtime_root, environment)
    report = runtime_root / "lean-integration-report.json"
    run_checked(
        [
            str(executable_path(installed, "ladon")),
            "--repo-root",
            str(fixture),
            "--root",
            "LadonFixture.lean",
            "--build",
            "--extraction-backend",
            "lean",
            "--format",
            "json",
            "--output",
            str(report),
        ],
        cwd=runtime_root,
        environment=environment,
    )
    assert_declaration_evidence(report)


def run_gate(candidate: str, required: bool) -> None:
    """Run or explicitly skip the selected candidate's reference Lean smoke."""

    with materialize_candidate(candidate, project_root()) as materialized:
        with runtime_directory("ladon-lean-gate-") as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            expected_lock = lock_digest(materialized.root)
            assert_no_absolute_maintainer_paths(materialized.root)
            if resolve_lake(environment) is None and not required:
                print("lean integration gate: SKIP: lake is unavailable")
                return
            run_real_lean(materialized.root, runtime_root, environment)
            assert_lock_unchanged(materialized.root, expected_lock)
    print("lean integration gate: PASS")


def main(argv: list[str] | None = None) -> int:
    """Run the gate and distinguish an allowed optional skip from failure."""

    args = build_parser().parse_args(argv)
    try:
        run_gate(args.candidate, args.required)
    except GateError as error:
        print(f"lean integration gate: FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
