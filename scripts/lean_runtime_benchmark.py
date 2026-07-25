#!/usr/bin/env python3
"""Measure synthetic Lean runtime cold, warm, and invalidation behavior."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from lean_runtime_gate import (
    fixture_root,
    project_root,
    provision_reference_toolchain,
)
from release_gate_runtime import run_checked, uv_executable
from release_gate_types import GateError


DEFAULT_OUTPUT = (
    project_root()
    / "openspec"
    / "changes"
    / "ladon-lean-extraction-runtime-hardening"
    / "benchmark-results.json"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the benchmark output and optional Quux metadata interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--quux-elapsed-seconds",
        type=float,
        help="Optional externally measured Quux timing, recorded separately.",
    )
    return parser


def run_scenario(
    fixture: Path,
    cache_dir: Path,
    output: Path,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    """Run one inventory extraction and summarize runtime/cache evidence."""

    started = perf_counter()
    run_checked(
        [
            uv_executable(),
            "run",
            "--locked",
            "ladon",
            "--repo-root",
            str(fixture),
            "--root",
            "LadonFixture",
            "--extraction-backend",
            "lean",
            "--lean-extraction-scope",
            "inventory",
            "--lean-cache-dir",
            str(cache_dir),
            "--format",
            "json",
            "--output",
            str(output),
        ],
        cwd=project_root(),
        environment=environment,
    )
    wall_seconds = perf_counter() - started
    payload = json.loads(output.read_text(encoding="utf-8"))
    phase = payload["phases"]["lean_extraction"]
    data = phase["data"]
    statuses = Counter(row["status"] for row in data["cache"])
    return {
        "wallSeconds": wall_seconds,
        "phaseSeconds": phase["elapsed_seconds"],
        "requested": data["requested"],
        "completed": data["completed"],
        "failed": data["failed"],
        "helperInvocations": phase["counters"]["helper_invocations"],
        "cacheStatuses": dict(sorted(statuses.items())),
        "cacheInvalidationReasons": sorted(
            {
                row["invalidationReason"]
                for row in data["cache"]
                if row["invalidationReason"]
            }
        ),
    }


def assert_benchmark_contract(results: Mapping[str, Mapping[str, Any]]) -> None:
    """Reject a benchmark that did not exercise each intended cache state."""

    cold = results["cold"]
    warm = results["warm"]
    invalidated = results["invalidated"]
    requested = int(cold["requested"])
    if int(cold["helperInvocations"]) < 1:
        raise GateError("cold benchmark did not invoke the Lean helper")
    if warm["cacheStatuses"].get("hit") != requested:
        raise GateError(f"warm benchmark did not hit every module: {warm}")
    if int(warm["helperInvocations"]) != 0:
        raise GateError(f"warm benchmark unexpectedly invoked a helper: {warm}")
    if invalidated["cacheStatuses"].get("miss", 0) < 2:
        raise GateError(
            f"source/import invalidation did not invalidate dependents: {invalidated}"
        )
    if invalidated["cacheStatuses"].get("hit", 0) < 1:
        raise GateError(f"invalidation benchmark omitted unaffected hit: {invalidated}")


def mutate_imported_source(fixture: Path) -> None:
    """Change one imported source without changing its declaration surface."""

    source = fixture / "LadonFixture" / "Core.lean"
    source.write_text(
        source.read_text(encoding="utf-8") + "\n-- cache invalidation benchmark\n",
        encoding="utf-8",
    )


def quux_result(elapsed_seconds: float | None) -> dict[str, Any]:
    """Keep optional Quux timing distinct from synthetic acceptance."""

    if elapsed_seconds is None:
        return {
            "status": "not_run",
            "elapsedSeconds": None,
            "reason": "optional external Quux timing was not supplied",
        }
    return {
        "status": "recorded_external",
        "elapsedSeconds": elapsed_seconds,
        "reason": "caller-supplied optional timing; not synthetic gate evidence",
    }


def run_benchmark(quux_elapsed_seconds: float | None) -> dict[str, Any]:
    """Build a temporary fixture copy and measure all synthetic scenarios."""

    environment = dict(os.environ)
    source_fixture = fixture_root()
    if not provision_reference_toolchain(
        source_fixture,
        environment,
        required=True,
    ):
        raise GateError("required Lean toolchain is unavailable")
    with tempfile.TemporaryDirectory(prefix="ladon-lean-benchmark-") as temporary:
        runtime = Path(temporary)
        fixture = runtime / "fixture"
        shutil.copytree(source_fixture, fixture, ignore=shutil.ignore_patterns(".lake"))
        lake = shutil.which("lake")
        if lake is None:
            raise GateError("required executable is unavailable: lake")
        run_checked([lake, "build"], cwd=fixture, environment=environment)
        cache = runtime / "cache"
        results = {
            "cold": run_scenario(
                fixture,
                cache,
                runtime / "cold.json",
                environment,
            ),
            "warm": run_scenario(
                fixture,
                cache,
                runtime / "warm.json",
                environment,
            ),
        }
        mutate_imported_source(fixture)
        results["invalidated"] = run_scenario(
            fixture,
            cache,
            runtime / "invalidated.json",
            environment,
        )
        assert_benchmark_contract(results)
        return {
            "schemaVersion": 1,
            "fixture": "tests/fixtures/lean_integration",
            "toolchain": source_fixture.joinpath("lean-toolchain")
            .read_text(encoding="utf-8")
            .strip(),
            "batchSize": 8,
            "scenarios": results,
            "quux": quux_result(quux_elapsed_seconds),
            "nonclaim": (
                "Synthetic timings characterize this fixture and host only; "
                "they are not a general performance guarantee."
            ),
        }


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark and write one deterministic-schema result."""

    args = build_parser().parse_args(argv)
    try:
        payload = run_benchmark(args.quux_elapsed_seconds)
    except GateError as exc:
        print(f"lean runtime benchmark: FAIL: {exc}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"lean runtime benchmark: PASS: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
