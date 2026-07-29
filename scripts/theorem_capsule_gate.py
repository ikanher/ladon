#!/usr/bin/env python3
"""Run installed-candidate theorem-capsule phases against pinned portable Lean."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Mapping

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


PHASES = ("planning", "materialization", "replay", "all")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, materialized directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Fail instead of skipping when the pinned Lake toolchain is unavailable.",
    )
    return parser


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_gate(candidate: str, phase: str, required: bool) -> None:
    with materialize_candidate(candidate, project_root()) as materialized:
        with runtime_directory("ladon-theorem-capsule-gate-") as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            lake = shutil.which("lake", path=environment.get("PATH"))
            if lake is None:
                if required:
                    raise GateError("required executable is unavailable: lake")
                print("theorem capsule gate: SKIP: lake is unavailable")
                return
            expected_lock = lock_digest(materialized.root)
            assert_no_absolute_maintainer_paths(materialized.root)
            installed = _installed_candidate(
                materialized.root,
                runtime_root,
                environment,
            )
            _run_phases(
                materialized.root,
                runtime_root,
                environment,
                lake,
                installed,
                phase,
            )
            assert_lock_unchanged(materialized.root, expected_lock)
    print(f"theorem capsule gate ({phase}): PASS")


def _installed_candidate(
    candidate_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
) -> Path:
    artifacts = build_distributions(candidate_root, runtime_root, environment)
    installed = install_wheel(artifacts, runtime_root, environment)
    assert_installed_import_origin(installed, runtime_root, environment)
    return executable_path(installed, "ladon")


def _run_phases(
    candidate_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
    lake: str,
    installed: Path,
    phase: str,
) -> None:
    fixture = runtime_root / "repository"
    shutil.copytree(
        candidate_root / "tests" / "fixtures" / "theorem_capsule",
        fixture,
        ignore=shutil.ignore_patterns(".lake"),
    )
    run_checked([lake, "build"], cwd=fixture, environment=environment)
    plan = runtime_root / "plan.json"
    run_checked(
        [
            str(installed),
            "theorem",
            "plan",
            "CapsuleFixture.chosen",
            "--repo-root",
            str(fixture),
            "--format",
            "json",
            "--output",
            str(plan),
        ],
        cwd=runtime_root,
        environment=environment,
    )
    _assert_plan(plan)
    if phase == "planning":
        return
    capsule = runtime_root / "capsule"
    run_checked(
        [
            str(installed),
            "theorem",
            "materialize",
            "--plan",
            str(plan),
            "--output",
            str(capsule),
            "--format",
            "json",
        ],
        cwd=runtime_root,
        environment=environment,
    )
    _assert_manifest(capsule / "capsule.json")
    if phase == "materialization":
        return
    unavailable = runtime_root / "repository-unavailable"
    fixture.rename(unavailable)
    receipt = runtime_root / "receipt.json"
    run_checked(
        [
            str(installed),
            "theorem",
            "replay",
            str(capsule),
            "--format",
            "json",
            "--output",
            str(receipt),
        ],
        cwd=runtime_root,
        environment=environment,
    )
    _assert_receipt(receipt)


def _assert_plan(path: Path) -> None:
    payload = _json_object(path)
    if payload.get("schema") != "ladon-theorem-capsule-plan-v1":
        raise GateError("installed theorem plan schema is missing")
    if payload.get("eligible") is not True:
        raise GateError("installed theorem plan is unexpectedly ineligible")
    if payload.get("target", {}).get("name") != "CapsuleFixture.chosen":
        raise GateError("installed theorem plan selected the wrong target")
    semantic = payload.get("semanticGraph", {})
    if semantic.get("status") != "complete" or semantic.get("nodeCount", 0) <= 64:
        raise GateError("installed theorem plan lacks complete semantic closure")


def _assert_manifest(path: Path) -> None:
    payload = _json_object(path)
    if payload.get("status") != "materialized_unverified":
        raise GateError("installed capsule manifest overstates verification")
    paths = {row.get("path") for row in payload.get("files", [])}
    required = {
        "plan.json",
        "CapsuleFixture.lean",
        "CapsuleFixture/Base.lean",
        "CapsuleFixture/Large.lean",
        "lean-toolchain",
        "lakefile.toml",
    }
    if not required <= paths:
        raise GateError("installed capsule manifest lacks required files")


def _assert_receipt(path: Path) -> None:
    payload = _json_object(path)
    if payload.get("status") != "verified":
        raise GateError(f"installed capsule did not verify: {payload.get('status')}")
    if payload.get("isolation", {}).get("passed") is not True:
        raise GateError("installed capsule lacks clean-room isolation evidence")
    if not all(payload.get("comparisons", {}).get("checks", {}).values()):
        raise GateError("installed capsule structural comparisons did not all pass")


def _json_object(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"artifact is unreadable: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GateError(f"artifact is not a JSON object: {path}")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_gate(args.candidate, args.phase, args.required)
    except GateError as error:
        print(f"theorem capsule gate: FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
