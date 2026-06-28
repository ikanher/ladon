"""Root-focused report findings derived from pure graph summaries."""

from __future__ import annotations

from typing import Any

from ladon.analysis.architecture_correlator import architecture_pressure_findings
from ladon.analysis.quality_baseline import calibrate_count


HOTSPOT_THRESHOLD = 5
LARGE_MODULE_LINE_THRESHOLD = 2000
MAX_FINDINGS_PER_KIND = 3


def summarize_findings(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    quality_baseline: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return concise findings from already-computed graph summaries."""

    findings: list[dict[str, Any]] = []
    findings.extend(module_fan_in_findings(module_dag))
    findings.extend(handwritten_module_fan_in_findings(module_dag))
    findings.extend(root_import_closure_findings(module_dag))
    findings.extend(duplicate_import_findings(module_dag))
    findings.extend(module_name_smell_findings(module_dag))
    findings.extend(large_handwritten_module_findings(module_dag))
    if declaration_graph:
        findings.extend(declaration_fan_findings(declaration_graph, "top_fan_in", "fan_in"))
        findings.extend(declaration_fan_findings(declaration_graph, "top_fan_out", "fan_out"))
        findings.extend(declaration_family_findings(declaration_graph))
        findings.extend(unresolved_reference_findings(declaration_graph))
        findings.extend(unreachable_declaration_findings(declaration_graph))
    findings.extend(architecture_pressure_findings(module_dag, declaration_graph))
    calibrate_findings(findings, quality_baseline)
    return findings


def module_fan_in_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag high module fan-in rows as architecture pressure."""

    rows = [
        finding(
            "module_fan_in_hotspot",
            row["module"],
            int(row["fan_in"]),
            f"{row['module']} is imported by {row['fan_in']} modules.",
            metric="module_fan_in",
        )
        for row in module_dag.get("top_fan_in", [])
        if int(row.get("fan_in", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def handwritten_module_fan_in_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag high fan-in among modules not tagged as generated."""

    rows = [
        finding(
            "handwritten_module_fan_in_hotspot",
            row["module"],
            int(row["fan_in"]),
            f"{row['module']} is imported by {row['fan_in']} non-generated graph modules.",
            metric="module_fan_in",
        )
        for row in module_dag.get("top_handwritten_fan_in", [])
        if int(row.get("fan_in", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def root_import_closure_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag direct root imports with large reachable closures."""

    rows = [
        finding(
            "root_import_closure_hotspot",
            f"{row['root']} -> {row['direct_import']}",
            int(row["reachable_module_count"]),
            root_import_closure_message(row),
            metric="root_import_closure",
        )
        for row in module_dag.get("root_direct_import_closures", [])
        if int(row.get("reachable_module_count", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def duplicate_import_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag modules that repeat the same import target."""

    rows = [
        finding(
            "duplicate_import_target",
            f"{row['module']} -> {row['target']}",
            int(row["count"]),
            duplicate_import_message(row),
        )
        for row in module_dag.get("duplicate_imports", [])
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def duplicate_import_message(row: dict[str, Any]) -> str:
    """Build a duplicate-import finding message with source evidence."""

    line_suffix = source_line_suffix(row.get("lines", []))
    return (
        f"{row['module']} imports {row['target']} {row['count']} times"
        f"{line_suffix}; {row.get('suggestedAction', 'deduplicate the import target')}."
    )


def source_line_suffix(lines: Any) -> str:
    """Render optional line evidence for source-level findings."""

    if not isinstance(lines, list) or not lines:
        return ""
    return " on lines " + ", ".join(str(line) for line in lines[:5])


def module_name_smell_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag module names that encode generator, parameter, or proof-case pressure."""

    rows = [
        finding(
            "module_name_smell",
            row["module"],
            len(row.get("reasonKinds", [])),
            module_name_smell_message(row),
        )
        for row in module_dag.get("module_name_smells", [])
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def module_name_smell_message(row: dict[str, Any]) -> str:
    """Build a concise module-name smell finding message."""

    reasons = ", ".join(str(kind) for kind in row.get("reasonKinds", [])[:5])
    action = row.get("suggestedAction", "review module naming")
    return f"{row['module']} has module-name review pressure ({reasons}); {action}."


def large_handwritten_module_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag very large source files after generated modules are filtered."""

    rows = [
        finding(
            "large_handwritten_module",
            row["module"],
            int(row["lineCount"]),
            f"{row['module']} has {row['lineCount']} source lines and is not tagged generated.",
            metric="module_line_count",
        )
        for row in module_dag.get("top_large_handwritten_modules", [])
        if int(row.get("lineCount", 0)) >= LARGE_MODULE_LINE_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def root_import_closure_message(row: dict[str, Any]) -> str:
    """Build a concise direct-import closure finding message."""

    return (
        f"{row['direct_import']} reaches {row['reachable_module_count']} known modules "
        f"from root {row['root']}."
    )


def declaration_fan_findings(
    declaration_graph: dict[str, Any],
    row_key: str,
    metric: str,
) -> list[dict[str, Any]]:
    """Flag high declaration fan-in or fan-out rows."""

    kind = f"declaration_{metric}_hotspot"
    rows = [
        finding(
            kind,
            row["declaration"],
            int(row[metric]),
            declaration_fan_message(row, metric),
            metric=f"declaration_{metric}",
        )
        for row in declaration_graph.get(row_key, [])
        if int(row.get(metric, 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def declaration_fan_message(row: dict[str, Any], metric: str) -> str:
    """Build a concise declaration fan finding message."""

    if metric == "fan_in":
        return f"{row['declaration']} is referenced by {row[metric]} known declarations."
    return f"{row['declaration']} references {row[metric]} known declarations."


def unresolved_reference_findings(declaration_graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag frequently unresolved reference candidates."""

    rows = actionable_unresolved_rows(declaration_graph)
    rows = [
        finding(
            "unresolved_reference_hotspot",
            row["candidate"],
            int(row["count"]),
            f"{row['candidate']} appears as an unresolved reference candidate {row['count']} times.",
        )
        for row in rows
        if int(row.get("count", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def declaration_family_findings(declaration_graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag repeated declaration-name families."""

    rows = [
        finding(
            "declaration_family_hotspot",
            row["suffix"],
            int(row["count"]),
            f"{row['count']} declarations share suffix {row['suffix']}.",
            metric="declaration_family_size",
        )
        for row in declaration_graph.get("declaration_name_families", [])
        if int(row.get("count", 0)) >= 3
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def actionable_unresolved_rows(declaration_graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Prefer classified actionable unresolved rows, fallback for old payloads."""

    rows = declaration_graph.get("top_actionable_unresolved_references")
    if rows is not None:
        return rows
    return declaration_graph.get("top_unresolved_references", [])


def unreachable_declaration_findings(declaration_graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag declarations not reachable from chosen declaration roots."""

    count = int(declaration_graph.get("declarations_not_reachable_from_chosen_roots_count", 0))
    if count == 0:
        return []
    return [
        finding(
            "unreachable_declarations",
            "chosen_roots",
            count,
            f"{count} declarations are not reachable from the chosen root declarations.",
        )
    ]


def calibrate_findings(
    findings: list[dict[str, Any]],
    quality_baseline: dict[str, Any] | None,
) -> None:
    """Attach baseline percentile/rank metadata where possible."""

    for row in findings:
        metric = row.pop("metric", None)
        if metric is None:
            continue
        baseline = calibrate_count(quality_baseline, metric, int(row["count"]))
        if baseline is not None:
            row["baseline"] = baseline


def finding(
    kind: str,
    subject: str,
    count: int,
    message: str,
    *,
    metric: str | None = None,
) -> dict[str, Any]:
    """Build one stable finding row."""

    row = {
        "kind": kind,
        "severity": "info",
        "subject": subject,
        "count": count,
        "message": message,
    }
    if metric is not None:
        row["metric"] = metric
    return row
