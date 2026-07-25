"""Result assembly and exact contract evaluation for the scale gate."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any, Mapping

from ladon.benchmark_process import platform_capabilities
from ladon.large_inventory_models import (
    ANALYSIS_COMMAND_TEMPLATE,
    LARGE_INVENTORY_GATE_SCHEMA,
    REPRESENTATIONS,
    RepresentationRun,
    ScaleCeilings,
)


def build_gate_artifact(
    cold: tuple[RepresentationRun, ...],
    warm: tuple[RepresentationRun, ...],
    *,
    candidate_identity: Mapping[str, Any],
    fixture_identity: Mapping[str, Any],
    ceilings: ScaleCeilings,
    sample_count: int,
) -> dict[str, Any]:
    """Evaluate measured runs and assemble the portable gate artifact."""

    candidate_id = str(candidate_identity.get("id", "unknown-candidate"))
    fixture_id = str(fixture_identity.get("id", "unknown-fixture"))
    checks = _resource_checks(
        (*cold, *warm),
        ceilings=ceilings,
        candidate_id=candidate_id,
        fixture_id=fixture_id,
    )
    cache_contract = _cache_contract(
        cold,
        warm,
        candidate_id=candidate_id,
        fixture_id=fixture_id,
    )
    determinism = _determinism_contract(
        cold,
        warm,
        candidate_id=candidate_id,
        fixture_id=fixture_id,
    )
    execution = _execution_contract(
        (*cold, *warm),
        candidate_id=candidate_id,
        fixture_id=fixture_id,
    )
    failures = [
        row for row in checks if not row["passed"]
    ] + execution["failures"] + cache_contract["failures"] + determinism["failures"]
    environment = reference_job_identity(
        tuple(candidate_identity.get("supportedPythonMinors", ()))
    )
    passed = not failures
    return {
        "artifactKind": "ladon_large_inventory_gate_results",
        "schema": LARGE_INVENTORY_GATE_SCHEMA,
        "schemaVersion": 1,
        "candidate": dict(candidate_identity),
        "fixture": dict(fixture_identity),
        "environment": environment,
        "protocol": {
            "sampleCount": sample_count,
            "temperatures": ["cold", "warm"],
            "representationsPerSample": list(REPRESENTATIONS),
            "cacheIsolation": "per_sample_and_representation",
            "ordinaryCliOnly": True,
            "projection": "review",
            "commandTemplate": list(ANALYSIS_COMMAND_TEMPLATE),
        },
        "ceilings": ceilings.to_dict(),
        "samples": {
            "cold": _sample_rows(cold, sample_count),
            "warm": _sample_rows(warm, sample_count),
        },
        "checks": checks,
        "execution": {
            key: value
            for key, value in execution.items()
            if key != "failures"
        },
        "cacheReuse": {
            key: value
            for key, value in cache_contract.items()
            if key != "failures"
        },
        "determinism": {
            key: value
            for key, value in determinism.items()
            if key != "failures"
        },
        "passed": passed,
        "referencePassed": passed and environment["matchesReferenceJob"],
        "failures": failures,
        "nonClaims": [
            "No resource measurements are combined into an aggregate score.",
            "A single result is one Python matrix cell, not evidence for unrun minors.",
            "Fixture measurements characterize analyzer behavior, not Lean theorem truth.",
        ],
    }


def _sample_rows(
    runs: tuple[RepresentationRun, ...],
    sample_count: int,
) -> list[dict[str, Any]]:
    return [
        {
            "sample": sample,
            "representations": {
                run.representation: run.to_dict()
                for run in runs
                if run.sample == sample
            },
        }
        for sample in range(1, sample_count + 1)
    ]


def _resource_checks(
    runs: tuple[RepresentationRun, ...],
    *,
    ceilings: ScaleCeilings,
    candidate_id: str,
    fixture_id: str,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for run in runs:
        wall_ceiling = (
            ceilings.cold_wall_seconds
            if run.temperature == "cold"
            else ceilings.warm_wall_seconds
        )
        checks.append(
            _metric_check(
                run,
                "wall_seconds",
                run.process.wall_seconds,
                wall_ceiling,
                "seconds",
                candidate_id,
                fixture_id,
            )
        )
        checks.append(
            _metric_check(
                run,
                "peak_rss_mib",
                run.process.peak_rss_mib,
                ceilings.peak_rss_mib,
                "MiB",
                candidate_id,
                fixture_id,
            )
        )
        size_ceiling = (
            ceilings.canonical_json_bytes
            if run.representation == "json"
            else ceilings.compact_text_bytes
        )
        checks.append(
            _metric_check(
                run,
                f"{run.representation}_bytes",
                run.output_bytes,
                size_ceiling,
                "bytes",
                candidate_id,
                fixture_id,
            )
        )
    return checks


def _metric_check(
    run: RepresentationRun,
    metric: str,
    observed: float | int | None,
    ceiling: float | int,
    unit: str,
    candidate_id: str,
    fixture_id: str,
) -> dict[str, Any]:
    supported = observed is not None
    return {
        "id": (
            f"{run.temperature}.{run.sample}."
            f"{run.representation}.{metric}"
        ),
        "temperature": run.temperature,
        "sample": run.sample,
        "representation": run.representation,
        "metric": metric,
        "observed": observed,
        "ceiling": ceiling,
        "unit": unit,
        "supported": supported,
        "passed": supported and observed <= ceiling,
        "candidateId": candidate_id,
        "fixtureId": fixture_id,
    }


def _cache_contract(
    cold: tuple[RepresentationRun, ...],
    warm: tuple[RepresentationRun, ...],
    *,
    candidate_id: str,
    fixture_id: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for run in (*cold, *warm):
        passed = (
            run.cache.observed
            and (
                run.cache.hit_count == 0
                if run.temperature == "cold"
                else run.cache.hit_count > 0
            )
        )
        row = {
            "id": (
                f"{run.temperature}.{run.sample}."
                f"{run.representation}.cache_outcome"
            ),
            "temperature": run.temperature,
            "sample": run.sample,
            "representation": run.representation,
            **run.cache.to_dict(),
            "passed": passed,
        }
        rows.append(row)
        if not passed:
            failures.append(
                {
                    **row,
                    "candidateId": candidate_id,
                    "fixtureId": fixture_id,
                }
            )
    return {
        "validated": not failures,
        "rows": rows,
        "failures": failures,
    }


def _execution_contract(
    runs: tuple[RepresentationRun, ...],
    *,
    candidate_id: str,
    fixture_id: str,
) -> dict[str, Any]:
    rows = [
        {
            "id": (
                f"{run.temperature}.{run.sample}."
                f"{run.representation}.process_success"
            ),
            "temperature": run.temperature,
            "sample": run.sample,
            "representation": run.representation,
            "returncode": run.process.returncode,
            "timedOut": run.process.timed_out,
            "error": run.error,
            "passed": run.error is None,
        }
        for run in runs
    ]
    failures = [
        {
            **row,
            "candidateId": candidate_id,
            "fixtureId": fixture_id,
        }
        for row in rows
        if not row["passed"]
    ]
    return {
        "validated": not failures,
        "rows": rows,
        "failures": failures,
    }


def _determinism_contract(
    cold: tuple[RepresentationRun, ...],
    warm: tuple[RepresentationRun, ...],
    *,
    candidate_id: str,
    fixture_id: str,
) -> dict[str, Any]:
    json_runs = [
        run for run in (*cold, *warm) if run.representation == "json"
    ]
    normalized_count, normalized_hashes, normalized_passed = (
        _determinism_dimension(json_runs, "normalized_sha256")
    )
    fingerprint_count, fingerprints, fingerprint_passed = (
        _determinism_dimension(json_runs, "analysis_fingerprint")
    )
    failures = _determinism_failures(
        (
            ("normalized_report_bytes", normalized_passed, normalized_hashes),
            ("analysis_fingerprint", fingerprint_passed, fingerprints),
        ),
        candidate_id=candidate_id,
        fixture_id=fixture_id,
    )
    return {
        "validated": not failures,
        "expectedJsonRuns": len(json_runs),
        "normalizedJsonRuns": normalized_count,
        "fingerprintedJsonRuns": fingerprint_count,
        "normalizedReportSha256": normalized_hashes,
        "analysisFingerprints": fingerprints,
        "failures": failures,
    }


def _determinism_dimension(
    runs: list[RepresentationRun],
    attribute: str,
) -> tuple[int, list[str], bool]:
    values = [
        value
        for run in runs
        if (value := getattr(run, attribute)) is not None
    ]
    distinct = sorted({str(value) for value in values})
    return len(values), distinct, len(values) == len(runs) and len(distinct) == 1


def _determinism_failures(
    dimensions: tuple[tuple[str, bool, list[str]], ...],
    *,
    candidate_id: str,
    fixture_id: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"determinism.{identifier}",
            "metric": identifier,
            "observed": observed,
            "expectedDistinctValues": 1,
            "passed": False,
            "candidateId": candidate_id,
            "fixtureId": fixture_id,
        }
        for identifier, passed, observed in dimensions
        if not passed
    ]


def reference_job_identity(
    supported_python_minors: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Return actual and required Ubuntu matrix-cell identity."""

    capabilities = platform_capabilities()
    release = _os_release()
    actual_minor = ".".join(platform.python_version_tuple()[:2])
    cpu_count = available_cpu_count()
    expected = {
        "os": "ubuntu",
        "versionId": "24.04",
        "architecture": "x86_64",
        "availableCpuCount": 4,
        "pythonMinors": list(supported_python_minors),
    }
    matches = (
        release.get("id") == expected["os"]
        and release.get("versionId") == expected["versionId"]
        and platform.machine() == expected["architecture"]
        and cpu_count == expected["availableCpuCount"]
        and (
            not supported_python_minors
            or actual_minor in supported_python_minors
        )
        and bool(capabilities["peakRss"]["supported"])
    )
    return {
        "expectedReferenceJob": expected,
        "actual": {
            **capabilities,
            "osRelease": release,
            "architecture": platform.machine(),
            "availableCpuCount": cpu_count,
            "pythonMinor": actual_minor,
        },
        "matchesReferenceJob": matches,
    }


def available_cpu_count() -> int | None:
    """Return scheduler-visible CPUs when supported, else the host count."""

    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        try:
            return len(affinity(0))
        except OSError:
            pass
    return os.cpu_count()


def _os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key.lower()] = value.strip().strip("\"'")
    return {
        "id": values.get("id", ""),
        "versionId": values.get("version_id", ""),
        "prettyName": values.get("pretty_name", ""),
    }


__all__ = [
    "available_cpu_count",
    "build_gate_artifact",
    "reference_job_identity",
]
