"""Root-focused report findings derived from pure graph summaries."""

from __future__ import annotations

import hashlib
from typing import Any

from ladon.analysis.architecture_correlator import architecture_pressure_findings
from ladon.analysis.quality_baseline import calibrate_count
from ladon.analysis.root_applicability import root_views_applicable
from ladon.finding_workflow import (
    aggregate_value_evidence,
    canonical_row_evidence,
)

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
    findings.extend(target_owned_module_fan_in_findings(module_dag))
    findings.extend(generated_family_pressure_findings(module_dag))
    findings.extend(root_import_closure_findings(module_dag))
    findings.extend(duplicate_import_findings(module_dag))
    findings.extend(module_name_smell_findings(module_dag))
    findings.extend(large_target_owned_module_findings(module_dag))
    if declaration_graph:
        findings.extend(declaration_fan_findings(declaration_graph, "top_fan_in", "fan_in"))
        findings.extend(declaration_fan_findings(declaration_graph, "top_fan_out", "fan_out"))
        findings.extend(declaration_family_findings(declaration_graph))
        findings.extend(unresolved_reference_findings(declaration_graph))
        findings.extend(unreachable_declaration_findings(declaration_graph))
    findings.extend(architecture_pressure_findings(module_dag, declaration_graph))
    findings = deduplicate_promoted_findings(findings)
    calibrate_findings(findings, quality_baseline)
    return [with_stable_finding_fields(row) for row in findings]


def module_fan_in_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag high module fan-in rows as architecture pressure."""

    rows = [
        finding(
            "module_fan_in_hotspot",
            row["module"],
            int(row["fan_in"]),
            (
                f"{row['module']} is imported by {row['fan_in']} modules "
                "across all discovered importers and targets."
            ),
            metric="module_fan_in",
            stable_key=fan_in_stable_key(row),
            promotion_population=str(
                row.get("population", "all_importers_to_all_targets")
            ),
            promotion_threshold=HOTSPOT_THRESHOLD,
            authority=str(row.get("authority", "module_import_graph")),
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "top_fan_in",
                    index,
                    row,
                    subject_field="module",
                    metric_field="fan_in",
                )
            ],
        )
        for index, row in enumerate(module_dag.get("top_fan_in", []))
        if int(row.get("fan_in", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def handwritten_module_fan_in_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapt the deprecated non-generated-tag compatibility population."""

    rows = [
        finding(
            "handwritten_module_fan_in_hotspot",
            row["module"],
            int(row["fan_in"]),
            (
                f"{row['module']} is imported by {row['fan_in']} modules in "
                "the legacy non-generated-tag population; this is not an "
                "authorship claim."
            ),
            metric="module_fan_in",
            stable_key=fan_in_stable_key(row),
            promotion_population=str(
                row.get(
                    "population",
                    "handwritten_importers_to_handwritten_targets",
                )
            ),
            promotion_threshold=HOTSPOT_THRESHOLD,
            authority=str(row.get("authority", "module_import_graph")),
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "top_handwritten_fan_in",
                    index,
                    row,
                    subject_field="module",
                    metric_field="fan_in",
                )
            ],
        )
        for index, row in enumerate(module_dag.get("top_handwritten_fan_in", []))
        if int(row.get("fan_in", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def target_owned_module_fan_in_findings(
    module_dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Prefer evidence-backed target ownership for owner-facing promotion."""

    rows = [
        finding(
            "target_owned_module_fan_in_hotspot",
            row["module"],
            int(row["fan_in"]),
            (
                f"{row['module']} is imported by {row['fan_in']} target-owned "
                "modules; imported, compiler-generated, project-generated, "
                "and unclassified importers are excluded."
            ),
            metric="module_fan_in",
            stable_key=fan_in_stable_key(row),
            promotion_population=str(
                row.get(
                    "population",
                    "target_owned_importers_to_target_owned_targets",
                )
            ),
            promotion_threshold=HOTSPOT_THRESHOLD,
            authority=str(
                row.get(
                    "authority",
                    "module_import_graph_and_population_policy",
                )
            ),
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "top_target_owned_fan_in",
                    index,
                    row,
                    subject_field="module",
                    metric_field="fan_in",
                )
            ],
        )
        for index, row in enumerate(module_dag.get("top_target_owned_fan_in", []))
        if int(row.get("fan_in", 0)) >= HOTSPOT_THRESHOLD
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def generated_family_pressure_findings(
    module_dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Promote only policy-configured generated-family review pressure."""

    calibration = module_dag.get("population_calibration")
    if not isinstance(calibration, dict):
        return []
    families = calibration.get("generatedFamilies")
    if not isinstance(families, list):
        return []
    findings = [
        generated_family_pressure_finding(row, index)
        for index, row in enumerate(families)
        if generated_family_crosses_threshold(row)
    ]
    return [row for row in findings if row is not None]


def generated_family_crosses_threshold(row: Any) -> bool:
    """Evaluate an explicit policy threshold without a built-in fallback."""

    if not isinstance(row, dict):
        return False
    threshold = row.get("reviewThreshold")
    value = row.get("reviewMetricValue")
    return (
        isinstance(threshold, dict)
        and isinstance(threshold.get("metric"), str)
        and positive_integer(threshold.get("atLeast"))
        and nonnegative_integer(value)
        and value >= threshold["atLeast"]
    )


def generated_family_pressure_finding(
    row: Any,
    index: int,
) -> dict[str, Any] | None:
    """Build one family finding with exact aggregate and population identity."""

    if not isinstance(row, dict):
        return None
    threshold = row["reviewThreshold"]
    metric = str(threshold["metric"])
    at_least = int(threshold["atLeast"])
    value = int(row["reviewMetricValue"])
    family_id = str(row.get("familyId", ""))
    aggregate_id = str(row.get("id", ""))
    result = finding(
        "generated_family_review_pressure",
        family_id,
        value,
        (
            f"Configured generated family {family_id} has {metric}={value}, "
            f"meeting its policy review threshold of at least {at_least}. "
            "This is review pressure only; it does not establish a generator "
            "defect, proof failure, theorem falsity, or generated-source "
            "freshness."
        ),
        metric=f"generated_family_{metric}",
        stable_key=(
            f"generated_family_review_pressure:{aggregate_id}:{metric}"
        ),
        promotion_population="project_generated",
        promotion_threshold=at_least,
        authority="generated_family_policy_and_module_inventory",
        evidence_refs=[
            generated_family_evidence(row, index),
        ],
    )
    result["review_metric"] = metric
    result["policy_digest"] = row.get("policyDigest")
    return result


def generated_family_evidence(
    row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    """Reference the exact canonical family aggregate used for promotion."""

    return {
        "type": "canonical-row",
        "section": "module_dag",
        "collection": "population_calibration.generatedFamilies",
        "index": index,
        "pointer": (
            "#/sections/module_dag/population_calibration/"
            f"generatedFamilies/{index}"
        ),
        "identity": {
            key: row[key]
            for key in (
                "id",
                "familyId",
                "population",
                "policyDigest",
                "reviewThreshold",
                "reviewMetricValue",
            )
            if key in row
        },
        "authority": "generated_family_policy_and_module_inventory",
    }


def positive_integer(value: Any) -> bool:
    """Return whether a JSON value is a positive, non-boolean integer."""

    return nonnegative_integer(value) and value > 0


def nonnegative_integer(value: Any) -> bool:
    """Return whether a JSON value is a non-negative, non-boolean integer."""

    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def root_import_closure_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag direct root imports with large reachable closures."""

    if not root_views_applicable(module_dag):
        return []
    rows = [
        finding(
            "root_import_closure_hotspot",
            f"{row['root']} -> {row['direct_import']}",
            int(row["reachable_module_count"]),
            root_import_closure_message(row),
            metric="root_import_closure",
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "root_direct_import_closures",
                    index,
                    row,
                    subject_field="direct_import",
                    metric_field="reachable_module_count",
                    extra_identity={"root": str(row["root"])},
                )
            ],
        )
        for index, row in enumerate(
            module_dag.get("root_direct_import_closures", [])
        )
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
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "duplicate_imports",
                    index,
                    row,
                    subject_field="module",
                    metric_field="count",
                    extra_identity={"target": str(row["target"])},
                )
            ],
        )
        for index, row in enumerate(module_dag.get("duplicate_imports", []))
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
    """Flag generated naming pressure without penalizing semantic domain names."""

    rows = [
        finding(
            "module_name_smell",
            row["module"],
            len(row.get("reasonKinds", [])),
            module_name_smell_message(row),
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "module_name_smells",
                    index,
                    row,
                    subject_field="module",
                    metric_field=None,
                )
            ],
        )
        for index, row in enumerate(module_dag.get("module_name_smells", []))
        if row.get("generated")
        or any(
            str(kind).startswith("generated_") for kind in row.get("reasonKinds", [])
        )
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def module_name_smell_message(row: dict[str, Any]) -> str:
    """Build a concise module-name smell finding message."""

    reasons = ", ".join(str(kind) for kind in row.get("reasonKinds", [])[:5])
    action = row.get("suggestedAction", "review module naming")
    return f"{row['module']} has module-name review pressure ({reasons}); {action}."


def large_target_owned_module_findings(
    module_dag: dict[str, Any],
) -> list[dict[str, Any]]:
    """Flag very large files in the exact calibrated target-owned population."""

    rows = [
        finding(
            "large_target_owned_module",
            row["module"],
            int(row["lineCount"]),
            (
                f"{row['module']} has {row['lineCount']} source lines in the "
                "calibrated target-owned population."
            ),
            metric="module_line_count",
            evidence_refs=[
                graph_row_evidence(
                    "module_dag",
                    "top_target_owned_large_modules",
                    index,
                    row,
                    subject_field="module",
                    metric_field="lineCount",
                )
            ],
        )
        for index, row in enumerate(
            module_dag.get("top_target_owned_large_modules", [])
        )
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
            evidence_refs=[
                graph_row_evidence(
                    "declaration_graph",
                    row_key,
                    index,
                    row,
                    subject_field="declaration",
                    metric_field=metric,
                )
            ],
        )
        for index, row in enumerate(declaration_graph.get(row_key, []))
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

    row_key, candidates = actionable_unresolved_rows(declaration_graph)
    rows = [
        finding(
            "unresolved_reference_hotspot",
            row["candidate"],
            int(row["count"]),
            f"{row['candidate']} appears as an unresolved reference candidate {row['count']} times.",
            evidence_refs=[
                graph_row_evidence(
                    "declaration_graph",
                    row_key,
                    index,
                    row,
                    subject_field="candidate",
                    metric_field="count",
                )
            ],
        )
        for index, row in enumerate(candidates)
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
            evidence_refs=[
                graph_row_evidence(
                    "declaration_graph",
                    "declaration_name_families",
                    index,
                    row,
                    subject_field="suffix",
                    metric_field="count",
                )
            ],
        )
        for index, row in enumerate(
            declaration_graph.get("declaration_name_families", [])
        )
        if int(row.get("count", 0)) >= 3
    ]
    return rows[:MAX_FINDINGS_PER_KIND]


def actionable_unresolved_rows(
    declaration_graph: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    """Prefer classified actionable unresolved rows, fallback for old payloads."""

    rows = declaration_graph.get("top_actionable_unresolved_references")
    if rows is not None:
        return "top_actionable_unresolved_references", rows
    return (
        "top_unresolved_references",
        declaration_graph.get("top_unresolved_references", []),
    )


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
            evidence_refs=[
                aggregate_value_evidence(
                    "declaration_graph",
                    "declarations_not_reachable_from_chosen_roots_count",
                    authority="declaration_graph",
                )
            ],
        )
    ]


def calibrate_findings(
    findings: list[dict[str, Any]],
    quality_baseline: dict[str, Any] | None,
) -> None:
    """Attach baseline percentile/rank metadata where possible."""

    for row in findings:
        metric = row.get("metric")
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
    stable_key: str | None = None,
    promotion_population: str | None = None,
    promotion_threshold: int | None = None,
    authority: str = "ladon_derived_heuristic",
    evidence_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one stable finding row."""

    row = {
        "kind": kind,
        "severity": "info",
        "subject": subject,
        "count": count,
        "message": message,
        "authority": authority,
    }
    if metric is not None:
        row["metric"] = metric
    if stable_key is not None:
        row["stable_key"] = stable_key
    if promotion_population is not None:
        row["promotion_population"] = promotion_population
    if promotion_threshold is not None:
        row["promotion_threshold"] = promotion_threshold
    if evidence_refs:
        row["evidenceRefs"] = evidence_refs
    return row


def graph_row_evidence(
    section: str,
    collection: str,
    index: int,
    row: dict[str, Any],
    *,
    subject_field: str,
    metric_field: str | None,
    extra_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reference an exact graph row with a compact identity cross-check."""

    identity = {subject_field: row.get(subject_field)}
    if metric_field is not None:
        identity[metric_field] = row.get(metric_field)
    identity.update(extra_identity or {})
    return canonical_row_evidence(
        section,
        collection,
        index,
        identity=identity,
        authority=str(row.get("authority", f"{section}_analysis")),
    )


def fan_in_stable_key(row: dict[str, Any]) -> str:
    """Identify equivalent fan-in promotion evidence across raw tables."""

    importers = ",".join(
        sorted(str(item) for item in row.get("sample_importers", []))
    )
    return (
        f"module_fan_in:{row.get('module', '')}:"
        f"{int(row.get('fan_in', 0))}:{importers}"
    )


def deduplicate_promoted_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Promote each semantic key once, preferring a truthful narrow label."""

    by_key: dict[str, tuple[int, dict[str, Any]]] = {}
    order: list[str] = []
    for row in findings:
        key = str(row.get("stable_key") or default_stable_key(row))
        rank = promotion_specificity(row)
        if key not in by_key:
            order.append(key)
            by_key[key] = (rank, row)
        elif rank > by_key[key][0]:
            by_key[key] = (rank, row)
    return [by_key[key][1] for key in order]


def promotion_specificity(row: dict[str, Any]) -> int:
    """Prefer exact calibrated populations over compatibility projections."""

    population = str(row.get("promotion_population", ""))
    return {
        "handwritten_importers_to_handwritten_targets": 1,
        "target_owned_importers_to_target_owned_targets": 2,
    }.get(population, 0)


def with_stable_finding_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Ensure every promoted finding exposes stable identity and authority."""

    normalized = dict(row)
    normalized.setdefault("stable_key", default_stable_key(normalized))
    normalized.setdefault("id", stable_finding_id(normalized))
    normalized.setdefault("authority", "ladon_derived_heuristic")
    return normalized


def default_stable_key(row: dict[str, Any]) -> str:
    """Return a semantic key independent of wording and report ordering."""

    return (
        f"{row.get('kind', 'finding')}:"
        f"{row.get('subject', '')}:"
        f"{row.get('count', 1)}"
    )


def stable_finding_id(row: dict[str, Any]) -> str:
    """Return a compact deterministic identifier for one semantic finding."""

    digest = hashlib.sha256(
        str(row["stable_key"]).encode("utf-8")
    ).hexdigest()[:16]
    return f"ladon.finding.{digest}"
