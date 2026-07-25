"""Labeled cache, process, and report-contract benchmark controls."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def evaluate_control_labels(
    results: Mapping[str, Any],
    labels: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Evaluate manifest control labels against one assembled suite result."""

    observations = control_observations(results)
    return [
        control_evidence(label, observations.get(str(label["oracle"]["signal"])))
        for label in labels
    ]


def control_evidence(
    label: Mapping[str, Any],
    observed: Any,
) -> dict[str, Any]:
    """Return one stable labeled control-evidence row."""

    expected = label["oracle"]["expected"]
    return {
        "id": label["id"],
        "class": label["class"],
        "metricFamily": label["metricFamily"],
        "signalKind": label["signalKind"],
        "expected": expected,
        "observed": observed,
        "passed": observed == expected,
        "rationale": label["rationale"],
    }


def control_observations(results: Mapping[str, Any]) -> dict[str, Any]:
    """Project stable observations from case and runtime-control results."""

    cases = list(results.get("cases", []))
    runtime = results.get("runtimeControls", {})
    timeout = runtime.get("timeout", {})
    cancellation = runtime.get("cancellation", {})
    lean_case = next(
        (case for case in cases if case.get("cache", {}).get("applicable")),
        {},
    )
    invalidation_rows = runtime.get("cacheInvalidation", [])
    return {
        "warm_cache_hit": bool(lean_case.get("cache", {}).get("warmHit")),
        "warm_helper_launches": lean_case.get("process", {}).get(
            "helperLaunchesWarm"
        ),
        "cache_invalidation_reasons": {
            row["input"]: row.get("observedReason")
            for row in invalidation_rows
        },
        "timeout_partial_report": bool(timeout.get("partialReportPresent")),
        "timeout_orphan_present": bool(timeout.get("orphanPresent")),
        "process_cleanup_passed": bool(
            timeout.get("passed") and cancellation.get("passed")
        ),
        "all_reports_schema_valid": all(
            case.get("stability", {}).get("schemaValid") for case in cases
        ),
        "normalized_mismatch_count": sum(
            not case.get("stability", {}).get("normalizedBytesEqual")
            for case in cases
        ),
        "all_report_size_budgets_passed": all(
            case.get("stability", {}).get("sizeBudgetsPassed")
            for case in cases
        ),
    }
