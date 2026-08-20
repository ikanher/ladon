"""Typed component measures used by architecture composite findings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ladon.finding_evidence import canonical_row_evidence

MODULE_COVERAGE_REF = "module_dag.modules"
DECLARATION_COVERAGE_REF = "declaration_graph.declarations"


def root_closure_signal(
    module_dag: Mapping[str, Any],
    index: int,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one exact root/import-closure component measure."""

    root = row_string(row, "root")
    direct_import = row_string(row, "direct_import")
    value = metric_integer(row, "reachable_module_count")
    authority = row_string(row, "authority") or "module_import_graph"
    return component_signal(
        "root_import_closure",
        f"{root} -> {direct_import}",
        value,
        unit="module",
        population="root_direct_import_closure",
        scope=f"{root} -> {direct_import}",
        denominator=known_denominator(
            module_dag.get("module_count"),
            unit="module",
            population="selected_module_inventory",
        ),
        aggregation="distinct_modules",
        authority=authority,
        coverage_ref=MODULE_COVERAGE_REF,
        evidence_ref=canonical_row_evidence(
            "module_dag",
            "root_direct_import_closures",
            index,
            identity={
                "root": root,
                "direct_import": direct_import,
                "reachable_module_count": value,
            },
            authority=authority,
        ),
    )


def top_root_closure(module_dag: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the largest valid direct root-import closure signal."""

    valid = [
        (index, row)
        for index, row in indexed_rows(
            module_dag,
            "root_direct_import_closures",
        )
        if _valid_root_closure(row)
    ]
    if not valid:
        return None
    index, row = min(valid, key=_closure_order_key)
    return root_closure_signal(module_dag, index, row)


def _valid_root_closure(row: Mapping[str, Any]) -> bool:
    return bool(
        row_string(row, "root")
        and row_string(row, "direct_import")
        and metric_integer(row, "reachable_module_count") >= 0
    )


def _closure_order_key(
    item: tuple[int, Mapping[str, Any]],
) -> tuple[int, str, str]:
    row = item[1]
    return (
        -metric_integer(row, "reachable_module_count"),
        row_string(row, "root"),
        row_string(row, "direct_import"),
    )


def top_metric_row(
    summary: Mapping[str, Any],
    row_key: str,
    metric: str,
) -> dict[str, Any] | None:
    """Return the largest valid metric row as a typed component signal."""

    rows = indexed_rows(summary, row_key)
    if not rows:
        return None
    index, row = min(
        rows,
        key=lambda item: (
            -metric_integer(item[1], metric),
            row_subject(item[1]),
        ),
    )
    return metric_row_signal(summary, row_key, index, row, metric)


def metric_row_signal(
    summary: Mapping[str, Any],
    row_key: str,
    index: int,
    row: Mapping[str, Any],
    metric: str,
    *,
    metric_override: str | None = None,
    population_override: str | None = None,
) -> dict[str, Any]:
    """Build one typed component measure from a canonical ranked row."""

    section = _metric_section(row_key)
    name = metric_override or metric_name(row_key, metric)
    subject = row_subject(row)
    authority = row_string(row, "authority") or _section_authority(section)
    measure = _metric_measure(
        summary,
        metric=metric,
        subject=subject,
        population_override=population_override,
    )
    return component_signal(
        name,
        subject,
        metric_integer(row, metric),
        authority=authority,
        evidence_ref=canonical_row_evidence(
            section,
            row_key,
            index,
            identity=metric_row_identity(row, metric),
            authority=authority,
        ),
        **measure,
    )


def _metric_section(row_key: str) -> str:
    if row_key == "declaration_name_families":
        return "declaration_graph"
    return "module_dag"


def _section_authority(section: str) -> str:
    if section == "declaration_graph":
        return "declaration_graph"
    return "module_import_graph"


def _metric_measure(
    summary: Mapping[str, Any],
    *,
    metric: str,
    subject: str,
    population_override: str | None,
) -> dict[str, Any]:
    if metric == "count":
        return _declaration_measure(summary, subject, population_override)
    return _import_edge_measure(summary, subject, population_override)


def _declaration_measure(
    summary: Mapping[str, Any],
    subject: str,
    population_override: str | None,
) -> dict[str, Any]:
    return {
        "unit": "declaration",
        "population": population_override or "declaration_name_family",
        "scope": f"declaration_family:{subject}",
        "denominator": known_denominator(
            summary.get("declaration_count"),
            unit="declaration",
            population="selected_declaration_inventory",
        ),
        "coverage_ref": DECLARATION_COVERAGE_REF,
        "aggregation": "distinct_declarations",
    }


def _import_edge_measure(
    summary: Mapping[str, Any],
    subject: str,
    population_override: str | None,
) -> dict[str, Any]:
    return {
        "unit": "import_edge",
        "population": (
            population_override or "selected_module_import_graph"
        ),
        "scope": f"module:{subject}",
        "denominator": known_denominator(
            summary.get("edge_count"),
            unit="import_edge",
            population="selected_module_import_graph",
        ),
        "coverage_ref": MODULE_COVERAGE_REF,
        "aggregation": "distinct_import_edges",
    }


def component_signal(
    metric: str,
    subject: str,
    value: Any,
    *,
    unit: str = "count",
    population: str = "unspecified",
    scope: str = "unspecified",
    denominator: Mapping[str, Any] | None = None,
    aggregation: str = "owner_reported_count",
    authority: str = "ladon_derived_heuristic",
    coverage_ref: str = "",
    evidence_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one named measure without combining unlike quantities."""

    row = {
        "metric": metric,
        "subject": subject,
        "value": int(value),
        "authority": authority,
        "coverageRef": coverage_ref,
        "measure": {
            "unit": unit,
            "population": population,
            "scope": scope,
            "denominator": dict(
                denominator
                or unknown_denominator(
                    unit=unit,
                    population=population,
                )
            ),
            "aggregation": aggregation,
        },
    }
    if evidence_ref is not None:
        row["evidenceRef"] = evidence_ref
    return row


def component_refs(
    signals: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return exact component references, rejecting missing pointer shapes."""

    return [
        dict(reference)
        for signal in signals
        for reference in [signal.get("evidenceRef")]
        if _is_local_reference(reference)
    ]


def _is_local_reference(reference: Any) -> bool:
    return (
        isinstance(reference, Mapping)
        and isinstance(reference.get("pointer"), str)
        and str(reference["pointer"]).startswith("#/sections/")
    )


def known_denominator(
    value: Any,
    *,
    unit: str,
    population: str,
) -> dict[str, Any]:
    """Return an exact denominator or an explicit unknown envelope."""

    normalized = nonnegative_integer_value(value)
    if normalized is None:
        return unknown_denominator(unit=unit, population=population)
    return {
        "status": "known",
        "value": normalized,
        "unit": unit,
        "population": population,
    }


def unknown_denominator(*, unit: str, population: str) -> dict[str, Any]:
    """Return an explicit unknown denominator for an absolute owner measure."""

    return {
        "status": "unknown",
        "value": None,
        "unit": unit,
        "population": population,
        "reason": "the owning analysis did not expose a denominator",
    }


def indexed_rows(
    summary: Mapping[str, Any],
    row_key: str,
) -> list[tuple[int, Mapping[str, Any]]]:
    """Return exact indexed mapping rows without accepting partial shapes."""

    rows = summary.get(row_key)
    if not isinstance(rows, list):
        return []
    return [
        (index, row)
        for index, row in enumerate(rows)
        if isinstance(row, Mapping)
    ]


def metric_integer(row: Mapping[str, Any], key: str) -> int:
    """Return one non-negative metric, or a sentinel for malformed rows."""

    value = nonnegative_integer_value(row.get(key))
    return value if value is not None else -1


def nonnegative_integer_value(value: Any) -> int | None:
    """Normalize a JSON non-negative integer without accepting booleans."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def row_string(row: Mapping[str, Any], key: str) -> str:
    """Return one non-empty row string or an empty sentinel."""

    value = row.get(key)
    return value if isinstance(value, str) and value else ""


def valid_string_sequence(value: Any) -> tuple[str, ...]:
    """Return a stable non-empty string sequence or an empty sentinel."""

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    if any(not isinstance(item, str) or not item for item in value):
        return ()
    return tuple(value)


def is_facade_member(value: Any) -> bool:
    """Return whether canonical module metadata carries the facade role."""

    if not isinstance(value, Mapping):
        return False
    roles = value.get("roles")
    if not isinstance(roles, list):
        return False
    return all(isinstance(role, str) for role in roles) and "facade" in roles


def metric_row_identity(
    row: Mapping[str, Any],
    metric: str,
) -> dict[str, Any]:
    """Return raw row fields that cross-check a canonical metric pointer."""

    for key in ("module", "declaration", "suffix", "candidate"):
        if key in row:
            return {key: row[key], metric: row.get(metric)}
    return {metric: row.get(metric)}


def metric_name(row_key: str, metric: str) -> str:
    """Return a stable component metric name."""

    names = {
        "top_fan_in": "module_fan_in",
        "top_fan_out": "module_fan_out",
        "top_facade_fan_out": "module_facade_fan_out",
        "top_implementation_fan_out": "module_implementation_fan_out",
        "declaration_name_families": "declaration_family_size",
    }
    return names.get(row_key, metric)


def row_subject(row: Mapping[str, Any]) -> str:
    """Return the best available row subject."""

    for key in ("module", "declaration", "suffix", "candidate"):
        if key in row:
            return str(row[key])
    return "unknown"


__all__ = [
    "DECLARATION_COVERAGE_REF",
    "MODULE_COVERAGE_REF",
    "component_refs",
    "component_signal",
    "indexed_rows",
    "is_facade_member",
    "known_denominator",
    "metric_integer",
    "metric_row_signal",
    "nonnegative_integer_value",
    "root_closure_signal",
    "row_string",
    "top_metric_row",
    "top_root_closure",
    "valid_string_sequence",
]
