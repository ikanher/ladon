"""Predicate-based regression checks for Ladon report payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


Expectation = dict[str, Any]
ResultRow = dict[str, Any]


BUILTIN_EXPECTATION_SUITES: dict[str, list[Expectation]] = {
    "quux/project-quux.json": [
        {"type": "acyclic"},
        {"type": "module_count_between", "min": 360, "max": 390},
        {"type": "top_module_fan_in", "module": "Quux.Basic", "max_rank": 1, "min_value": 90},
        {"type": "top_module_fan_out", "module": "Quux.Problems", "max_rank": 1, "min_value": 80},
        {"type": "finding_kind_present", "kind": "composite_import_pressure"},
        {"type": "finding_kind_present", "kind": "facade_fanout_pressure"},
    ],
    "quux/owner-propagation-lean.json": [
        {"type": "acyclic"},
        {"type": "declaration_count_between", "min": 8, "max": 20},
        {
            "type": "declaration_fan_in",
            "declaration": "Quux.Semantics.PropagationAlgebra",
            "max_rank": 1,
            "min_value": 6,
        },
        {"type": "finding_kind_absent", "kind": "unresolved_reference_hotspot"},
        {"type": "proof_similarity_absent"},
    ],
    "matrix-factorization/project-mf.json": [
        {"type": "acyclic"},
        {"type": "module_count_between", "min": 500, "max": 560},
        {"type": "top_module_fan_in", "module": "Mf.DP.Sensitivity", "max_rank": 1, "min_value": 10},
        {"type": "top_module_fan_out", "module": "Mf.NTK", "max_rank": 1, "min_value": 20},
    ],
    "matrix-factorization/owner-bifr-packed-profile-lean.json": [
        {"type": "finding_kind_present", "kind": "root_import_closure_hotspot"},
        {"type": "finding_kind_present", "kind": "proof_family_import_pressure"},
        {
            "type": "declaration_fan_in",
            "declaration": "Mf.DP.bifrHalfLinePackedProfileIndex",
            "max_rank": 1,
            "min_value": 10,
        },
        {"type": "declaration_family_present", "suffix": "ge_one_add_firstLag", "min_count": 5},
        {"type": "declaration_family_present", "suffix": "nonneg", "min_count": 5},
        {"type": "proof_similarity_suffix_present", "suffix": "eq_forward"},
        {"type": "proof_similarity_suffix_present", "suffix": "ge_one"},
        {"type": "proof_similarity_suffix_present", "suffix": "last"},
        {"type": "proof_similarity_suffix_present", "suffix": "nonneg"},
        {"type": "proof_similarity_suffix_present", "suffix": "rev"},
    ],
    "matrix-factorization/owner-bifr-r37-packet.json": [
        {"type": "packet_status", "status": "partial", "score": 3, "max_score": 6},
    ],
}


ROOT_MATRIX_EXPECTATION_SUITES: dict[str, list[Expectation]] = {
    "quux/quux-project.json": [
        {"type": "acyclic"},
        {"type": "module_count_between", "min": 360, "max": 390},
        {"type": "top_module_fan_in", "module": "Quux.Basic", "max_rank": 1, "min_value": 90},
        {"type": "top_module_fan_out", "module": "Quux.Problems", "max_rank": 1, "min_value": 80},
        {"type": "review_region_present", "kind": "import_pressure_region", "min_signals": 5},
    ],
    "quux/quux-propagation.json": [
        {"type": "declaration_count_between", "min": 8, "max": 20},
        {
            "type": "declaration_fan_in",
            "declaration": "Quux.Semantics.PropagationAlgebra",
            "max_rank": 1,
            "min_value": 6,
        },
        {"type": "finding_kind_absent", "kind": "unresolved_reference_hotspot"},
        {"type": "root_scope_classification", "classification": "narrow_owner"},
    ],
    "quux/quux-bifr-rmse-problem.json": [
        {"type": "module_count_between", "min": 360, "max": 390},
        {"type": "declaration_count_between", "min": 8, "max": 20},
        {"type": "review_region_present", "kind": "import_context_region", "min_signals": 2},
    ],
    "matrix-factorization/mf-project.json": [
        {"type": "module_count_between", "min": 500, "max": 560},
        {"type": "top_module_fan_in", "module": "Mf.DP.Sensitivity", "max_rank": 1, "min_value": 10},
        {"type": "top_module_fan_out", "module": "Mf.NTK", "max_rank": 1, "min_value": 20},
        {"type": "root_scope_classification", "classification": "public_root_narrow_inventory"},
    ],
    "matrix-factorization/mf-bifr-packed-profile.json": [
        {"type": "root_scope_classification", "classification": "narrow_owner_broad_import"},
        {"type": "finding_kind_present", "kind": "proof_family_import_pressure"},
        {"type": "review_region_present", "kind": "import_pressure_region", "min_signals": 3},
        {"type": "review_region_present", "kind": "proof_family_region", "min_signals": 10},
        {
            "type": "declaration_fan_in",
            "declaration": "Mf.DP.bifrHalfLinePackedProfileIndex",
            "max_rank": 1,
            "min_value": 10,
        },
        {"type": "declaration_family_present", "suffix": "ge_one_add_firstLag", "min_count": 5},
        {"type": "declaration_family_present", "suffix": "nonneg", "min_count": 5},
    ],
    "matrix-factorization/mf-gaussian-core.json": [
        {"type": "module_count_between", "min": 500, "max": 560},
        {"type": "declaration_count_between", "min": 25, "max": 45},
        {"type": "finding_kind_absent", "kind": "unresolved_reference_hotspot"},
        {"type": "review_region_present", "kind": "import_context_region", "min_signals": 2},
    ],
    "matrix-factorization/mf-bsr-factor-core.json": [
        {"type": "declaration_count_between", "min": 50, "max": 80},
        {"type": "finding_kind_present", "kind": "proof_family_import_pressure"},
        {"type": "review_region_present", "kind": "proof_family_region", "min_signals": 10},
    ],
    "matrix-factorization/mf-optimization-ftrl.json": [
        {"type": "declaration_count_between", "min": 10, "max": 25},
        {"type": "root_scope_classification", "classification": "narrow_owner"},
    ],
}


def expectation_suites_by_name() -> dict[str, dict[str, list[Expectation]]]:
    """Return named built-in expectation suites."""

    return {
        "live": BUILTIN_EXPECTATION_SUITES,
        "root-matrix": ROOT_MATRIX_EXPECTATION_SUITES,
    }


def evaluate_reports_root(
    reports_root: Path,
    suites: dict[str, list[Expectation]] | None = None,
) -> list[ResultRow]:
    """Evaluate report suites rooted at a generated-report directory."""

    return evaluate_report_suite(reports_root, suites or BUILTIN_EXPECTATION_SUITES)


def evaluate_report_suite(
    reports_root: Path,
    suites: dict[str, list[Expectation]],
) -> list[ResultRow]:
    """Evaluate expectations for several report files."""

    rows: list[ResultRow] = []
    for relative_path, expectations in sorted(suites.items()):
        report_path = reports_root / relative_path
        if not report_path.exists():
            rows.append(missing_report_row(relative_path))
            continue
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        rows.extend(evaluate_expectations(payload, expectations, report_name=relative_path))
    return rows


def evaluate_expectations(
    payload: dict[str, Any],
    expectations: list[Expectation],
    *,
    report_name: str,
) -> list[ResultRow]:
    """Evaluate one report payload against expectation dictionaries."""

    return [
        evaluate_expectation(payload, expectation, report_name=report_name)
        for expectation in expectations
    ]


def evaluate_expectation(
    payload: dict[str, Any],
    expectation: Expectation,
    *,
    report_name: str,
) -> ResultRow:
    """Evaluate one expectation and return a structured result row."""

    predicate = str(expectation["type"])
    try:
        passed, message = predicate_dispatch()[predicate](payload, expectation)
    except KeyError:
        passed, message = False, f"unknown predicate type: {predicate}"
    return {
        "report": report_name,
        "predicate": predicate,
        "passed": passed,
        "message": message,
    }


def predicate_dispatch() -> dict[str, Any]:
    """Return predicate implementations by expectation type."""

    return {
        "acyclic": check_acyclic,
        "module_count_between": check_module_count_between,
        "top_module_fan_in": check_top_module_fan_in,
        "top_module_fan_out": check_top_module_fan_out,
        "finding_kind_present": check_finding_kind_present,
        "finding_kind_absent": check_finding_kind_absent,
        "root_scope_classification": check_root_scope_classification,
        "review_region_present": check_review_region_present,
        "declaration_count_between": check_declaration_count_between,
        "declaration_fan_in": check_declaration_fan_in,
        "declaration_family_present": check_declaration_family_present,
        "proof_similarity_suffix_present": check_proof_similarity_suffix_present,
        "proof_similarity_absent": check_proof_similarity_absent,
        "packet_status": check_packet_status,
    }


def check_acyclic(payload: dict[str, Any], _expectation: Expectation) -> tuple[bool, str]:
    value = bool(payload.get("module_dag", {}).get("acyclic"))
    return value, f"acyclic={value}"


def check_module_count_between(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    value = int(payload.get("module_dag", {}).get("module_count", -1))
    return in_range(value, expectation), f"module_count={value}"


def check_top_module_fan_in(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    return check_ranked_row(
        payload.get("module_dag", {}).get("top_fan_in", []),
        name_key="module",
        value_key="fan_in",
        expected_name=str(expectation["module"]),
        expectation=expectation,
    )


def check_top_module_fan_out(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    return check_ranked_row(
        payload.get("module_dag", {}).get("top_fan_out", []),
        name_key="module",
        value_key="fan_out",
        expected_name=str(expectation["module"]),
        expectation=expectation,
    )


def check_finding_kind_present(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    kinds = [finding.get("kind") for finding in payload.get("findings", [])]
    expected = expectation["kind"]
    return expected in kinds, f"finding kinds={kinds}"


def check_finding_kind_absent(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    kinds = [finding.get("kind") for finding in payload.get("findings", [])]
    expected = expectation["kind"]
    return expected not in kinds, f"finding kinds={kinds}"


def check_root_scope_classification(
    payload: dict[str, Any],
    expectation: Expectation,
) -> tuple[bool, str]:
    expected = str(expectation["classification"])
    classes = [
        finding.get("root_scope", {}).get("classification")
        for finding in payload.get("findings", [])
        if finding.get("kind") == "root_scope_pressure"
    ]
    return expected in classes, f"root_scope classifications={classes}"


def check_review_region_present(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    expected = str(expectation["kind"])
    row = find_row(payload.get("review_regions", []), "kind", expected)
    if row is None:
        return False, f"review region {expected} missing"
    signals = int(row.get("signal_count", 0))
    min_signals = int(expectation.get("min_signals", 1))
    return signals >= min_signals, f"{expected} signals={signals}"


def check_declaration_count_between(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    value = int(payload.get("declaration_graph", {}).get("declaration_count", -1))
    return in_range(value, expectation), f"declaration_count={value}"


def check_declaration_fan_in(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    return check_ranked_row(
        payload.get("declaration_graph", {}).get("top_fan_in", []),
        name_key="declaration",
        value_key="fan_in",
        expected_name=str(expectation["declaration"]),
        expectation=expectation,
    )


def check_declaration_family_present(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    row = find_row(
        payload.get("declaration_graph", {}).get("declaration_name_families", []),
        "suffix",
        expectation["suffix"],
    )
    if row is None:
        return False, f"suffix {expectation['suffix']} missing"
    count = int(row.get("count", 0))
    return count >= int(expectation.get("min_count", 1)), f"family count={count}"


def check_proof_similarity_suffix_present(
    payload: dict[str, Any],
    expectation: Expectation,
) -> tuple[bool, str]:
    rows = payload.get("declaration_graph", {}).get("proof_family_similarity_candidates", [])
    suffixes = [row.get("suffix") for row in rows]
    expected = expectation["suffix"]
    return expected in suffixes, f"proof similarity suffixes={suffixes}"


def check_proof_similarity_absent(payload: dict[str, Any], _expectation: Expectation) -> tuple[bool, str]:
    rows = payload.get("declaration_graph", {}).get("proof_family_similarity_candidates", [])
    return not rows, f"proof similarity count={len(rows)}"


def check_packet_status(payload: dict[str, Any], expectation: Expectation) -> tuple[bool, str]:
    packets = payload.get("packet_evidence", [])
    if not packets:
        return False, "packet_evidence missing"
    packet = packets[0]
    expected = {
        "status": expectation.get("status"),
        "score": expectation.get("score"),
        "max_score": expectation.get("max_score"),
    }
    actual = {key: packet.get(key) for key in expected}
    return actual == expected, f"packet={actual}"


def check_ranked_row(
    rows: list[dict[str, Any]],
    *,
    name_key: str,
    value_key: str,
    expected_name: str,
    expectation: Expectation,
) -> tuple[bool, str]:
    """Check that a named row appears early enough with enough value."""

    row = find_row(rows, name_key, expected_name)
    if row is None:
        return False, f"{expected_name} missing"
    rank = rows.index(row) + 1
    value = int(row.get(value_key, 0))
    passed = rank <= int(expectation.get("max_rank", len(rows))) and value >= int(
        expectation.get("min_value", 0)
    )
    return passed, f"{expected_name} rank={rank} {value_key}={value}"


def find_row(rows: list[dict[str, Any]], key: str, expected: Any) -> dict[str, Any] | None:
    """Return first row whose key equals expected."""

    return next((row for row in rows if row.get(key) == expected), None)


def in_range(value: int, expectation: Expectation) -> bool:
    """Return whether value satisfies inclusive min/max bounds."""

    return int(expectation.get("min", value)) <= value <= int(expectation.get("max", value))


def missing_report_row(relative_path: str) -> ResultRow:
    """Return the stable failure row for absent report files."""

    return {
        "report": relative_path,
        "predicate": "report_exists",
        "passed": False,
        "message": "missing report file",
    }
