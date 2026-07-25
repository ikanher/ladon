#!/usr/bin/env python3
"""Run Ladon's portable signal benchmarks against an explicit candidate."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from typing import TextIO

import jsonschema

from release_gate_candidate import materialize_candidate
from release_gate_distribution import (
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

from ladon.benchmark_contract import (
    BenchmarkContractError,
    load_benchmark_manifest,
)
from ladon.benchmark_control_oracles import evaluate_control_labels
from ladon.benchmark_runtime_cases import run_runtime_cases
from ladon.benchmark_suite import BenchmarkFailure, run_portable_suite


MANIFEST_PATH = Path("tests/fixtures/benchmark_harness/manifest-v1.json")
REPORT_SCHEMA_PATH = Path("src/ladon/schemas/ladon-report-v2.schema.json")


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit-candidate benchmark interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        required=True,
        help="Explicit treeish, materialized directory, or the sentinel 'worktree'.",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Fail unless every portable required case and promotion gate passes.",
    )
    parser.add_argument(
        "--output",
        help="Optional machine-readable JSON path; JSON is printed to stdout otherwise.",
    )
    return parser


def project_root() -> Path:
    """Return the repository containing this gate script."""

    return Path(__file__).resolve().parents[1]


def run_benchmarks(candidate: str, *, required: bool) -> dict:
    """Build, install, and benchmark one explicitly selected candidate."""

    with materialize_candidate(candidate, project_root()) as materialized:
        with runtime_directory("ladon-benchmarks-") as temporary:
            runtime_root = Path(temporary)
            environment = sanitized_environment(runtime_root, materialized.root)
            expected_lock = lock_digest(materialized.root)
            assert_no_absolute_maintainer_paths(materialized.root)
            manifest = load_benchmark_manifest(materialized.root / MANIFEST_PATH)
            validate_manifest_schema(materialized.root, manifest)
            report_validator = report_schema_validator(materialized.root)
            artifacts = build_distributions(
                materialized.root,
                runtime_root,
                environment,
            )
            installed = install_wheel(artifacts, runtime_root, environment)
            results = run_portable_suite(
                materialized.root,
                runtime_root,
                executable_path(installed, "ladon"),
                environment,
                manifest,
                report_validator,
            )
            runtime_cases = run_runtime_cases(
                materialized.root,
                runtime_root,
                executable_path(installed, "ladon"),
                installed_helper_path(installed.python, runtime_root, environment),
                environment,
                required_lean_case(manifest),
                manifest["budgets"],
            )
            attach_runtime_cases(
                results,
                runtime_cases,
                manifest["controlLabels"],
            )
            assert_lock_unchanged(materialized.root, expected_lock)
            if required and not results["passed"]:
                raise GateError("one or more required benchmark contracts failed")
            return results


def installed_helper_path(
    installed_python: Path,
    runtime_root: Path,
    environment: dict[str, str],
) -> Path:
    """Resolve the candidate helper through its isolated installed package."""

    code = (
        "from importlib import resources; "
        "print(resources.files('ladon').joinpath('lean', "
        "'ladon_parser_helper.lean'))"
    )
    result = run_checked(
        [str(installed_python), "-c", code],
        cwd=runtime_root,
        environment=environment,
        capture_output=True,
    )
    return Path(result.stdout.strip())


def required_lean_case(manifest: dict) -> dict:
    """Return the required installed Lean benchmark case."""

    return next(
        case
        for case in manifest["cases"]
        if case.get("required") and case.get("setup") == "fake_lake"
    )


def attach_runtime_cases(
    results: dict,
    runtime_cases: dict,
    control_labels: list[dict],
) -> None:
    """Attach cache/process evidence without creating a composite score."""

    results["runtimeControls"] = runtime_cases
    control_evidence = evaluate_control_labels(results, control_labels)
    results["controlEvidence"] = control_evidence
    results["metricFamilies"]["cache"]["invalidationCases"] = len(
        runtime_cases["cacheInvalidation"]
    )
    results["metricFamilies"]["cache"]["failedInvalidationCases"] = sum(
        not row["passed"]
        for row in runtime_cases["cacheInvalidation"]
    )
    results["metricFamilies"]["process"]["timeoutPassed"] = runtime_cases[
        "timeout"
    ]["passed"]
    results["metricFamilies"]["process"]["cancellationPassed"] = runtime_cases[
        "cancellation"
    ]["passed"]
    results["passed"] = (
        results["passed"]
        and runtime_cases["passed"]
        and all(row["passed"] for row in control_evidence)
    )


def validate_manifest_schema(candidate_root: Path, manifest: dict) -> None:
    """Validate the candidate manifest against its candidate schema."""

    schema = json.loads(
        (
            candidate_root
            / "src/ladon/schemas/ladon-benchmark-manifest-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)


def report_schema_validator(candidate_root: Path):
    """Return a callable backed by the selected candidate's report schema."""

    schema = json.loads(
        (candidate_root / REPORT_SCHEMA_PATH).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    return validator.validate


def emit_results(results: dict, output: str | None) -> None:
    """Emit stable machine JSON and a compact separated-family summary."""

    content = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"benchmark results: {path}")
    else:
        print(content, end="")
    print_summary(results, stream=sys.stdout if output else sys.stderr)


def print_summary(results: dict, *, stream: TextIO = sys.stdout) -> None:
    """Print one compact summary without inventing a composite score."""

    families = results["metricFamilies"]
    print(
        "benchmark summary: "
        f"correctness failures={families['correctness']['failedOracleCount']}; "
        f"coverage={families['coverage']['hitCount']}/"
        f"{families['coverage']['expectedCount']}; "
        f"cold={families['runtime']['maxColdWallSeconds']:.3f}s; "
        f"warm={families['runtime']['maxWarmWallSeconds']:.3f}s; "
        f"peak-rss={families['memory']['maxPeakRssMiB']:.3f}MiB; "
        f"warm-cache-hits={families['cache']['warmHitCount']}; "
        f"stability failures={families['stability']['failedCaseCount']}",
        file=stream,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the gate and render deterministic failures."""

    args = build_parser().parse_args(argv)
    try:
        log_context = (
            nullcontext()
            if args.output
            else redirect_stdout(sys.stderr)
        )
        with log_context:
            results = run_benchmarks(args.candidate, required=args.required)
        emit_results(results, args.output)
    except (
        BenchmarkContractError,
        BenchmarkFailure,
        GateError,
        jsonschema.ValidationError,
        OSError,
        ValueError,
    ) as error:
        print(f"ladon benchmarks: FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
