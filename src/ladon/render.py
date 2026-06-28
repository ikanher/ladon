"""JSON and text rendering for Ladon's clean-core report.

Renderers consume already-computed report data. They do not inspect target
repositories or run analysis.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ladon.extraction import ModuleDiscovery


POLICY_DETAIL_FINDING_KINDS = {
    "architecture_policy.direct_forbidden_import",
    "architecture_policy.transitive_forbidden_import",
    "architecture_policy.shared_dependency_candidate",
    "source_pattern.invalid_policy",
    "source_pattern.match",
}


def generated_timestamp(override: str | None = None) -> str:
    """Return a deterministic timestamp override or the current UTC time."""

    if override:
        return override
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def report_payload(
    discovery: ModuleDiscovery,
    module_dag: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build the stable clean-core JSON payload for one run."""

    return {
        "metadata": {
            "tool_name": "ladon",
            "tool_version": "0.1.0",
            "report_version": "clean-core-1",
            "generated_at_utc": generated_timestamp(generated_at_utc),
            "repo_root": str(discovery.repo_root),
            "analysis_root": str(discovery.analysis_root_file),
            "analysis_root_module": discovery.analysis_root_module,
            "inventory_root": discovery.inventory_root,
        },
        "warnings": warnings or [],
        "module_dag": module_dag,
    }


def render_text(payload: dict[str, Any]) -> str:
    """Render a concise human-readable summary of the clean-core payload."""

    metadata = payload["metadata"]
    dag = payload["module_dag"]
    lines = [
        "Ladon Clean-Core Report",
        f"Root: {metadata['repo_root']}",
        f"Analysis root: {metadata['analysis_root_module']}",
        "",
        "Module DAG",
        f"- modules: {dag['module_count']}",
        f"- edges: {dag['edge_count']}",
        f"- acyclic: {dag['acyclic']}",
        f"- topological layers: {dag['topological_layer_count']}",
        f"- facade modules: {dag['facade_module_count']}",
        f"- generated modules: {dag.get('generated_module_count', 0)}",
        f"- duplicate import targets: {dag.get('duplicate_import_count', 0)}",
        "",
    ]
    lines.extend(warning_lines(payload.get("warnings", [])))
    lines.extend(architecture_policy_lines(payload.get("architecture_policy")))
    lines.extend(source_pattern_lines(payload.get("source_patterns")))
    lines.extend(finding_lines(payload.get("findings", [])))
    lines.extend(quality_baseline_lines(payload.get("quality_baseline")))
    lines.extend(packet_evidence_lines(payload.get("packet_evidence", [])))
    lines.extend(review_region_lines(payload.get("review_regions", [])))
    lines.extend(declaration_graph_lines(payload.get("declaration_graph")))
    lines.extend(timing_lines(payload.get("pipeline", {}).get("timings", {})))
    lines.extend(module_dag_detail_lines(dag))
    return "\n".join(lines).rstrip() + "\n"


def warning_lines(warnings: list[str]) -> list[str]:
    """Render support-boundary warnings, if any."""

    if not warnings:
        return []
    return ["Warnings", *[f"- {warning}" for warning in warnings], ""]


def architecture_policy_lines(policy: dict[str, Any] | None) -> list[str]:
    """Render architecture policy summary rows when supplied."""

    if not policy:
        return []
    summary = policy.get("summary", {})
    finding_count = sum(int(value) for value in summary.values())
    lines = [
        "Architecture Policy",
        f"- policy: {policy.get('policyId', '') or '(unnamed)'}",
        f"- groups: {policy.get('groupCount', 0)}",
        f"- rules: {policy.get('ruleCount', 0)}",
        f"- findings: {finding_count}",
    ]
    lines.extend(architecture_pair_lines(policy.get("directPairSummary", [])))
    lines.extend(architecture_context_lines(policy.get("directContextSummary", [])))
    lines.extend(architecture_offending_file_lines(policy.get("directOffendingFileSummary", [])))
    lines.extend(architecture_shared_dependency_lines(policy.get("sharedDependencySummary", [])))
    lines.extend(
        f"- {kind}: {count}"
        for kind, count in sorted(summary.items())
    )
    return [*lines, ""]


def architecture_pair_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render top architecture policy pair counts."""

    if not rows:
        return []
    return [
        f"- pair {row['sourceGroup']} -> {row['targetGroup']}: {row['uniqueDirectEdgeCount']}"
        for row in rows[:5]
    ]


def architecture_context_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render direct policy finding context counts."""

    if not rows:
        return []
    return [
        (
            f"- context {row['policyContext']}: {row['count']} "
            f"triage={','.join(row.get('triageSeverities', []))}"
        )
        for row in rows[:5]
    ]


def architecture_offending_file_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render files with the most direct policy violations."""

    if not rows:
        return []
    return [
        architecture_offending_file_line(row)
        for row in rows[:5]
    ]


def architecture_offending_file_line(row: dict[str, Any]) -> str:
    """Render one compact offending-file policy row."""

    samples = row.get("sampleImports", [])
    sample = architecture_import_sample(samples[0]) if samples else ""
    return (
        f"- file {row.get('sourcePath') or row.get('sourceModule')}: "
        f"{row['uniqueDirectEdgeCount']} direct violations{sample}"
    )


def architecture_import_sample(sample: dict[str, Any]) -> str:
    """Render one import sample from an offending-file summary."""

    line = f":{sample['line']}" if sample.get("line") is not None else ""
    import_text = str(sample.get("importText", ""))
    if import_text:
        return f" sample line{line} {import_text}"
    return ""


def architecture_shared_dependency_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render top shared-dependency extraction candidates."""

    if not rows:
        return []
    return [
        (
            f"- common-layer candidate {row['targetModule']}: "
            f"confidence={row.get('confidence', 'low')} "
            f"scope={row.get('dependencyScope', 'policy_targets')} "
            f"groups={','.join(row['sourceGroups'])} "
            f"importers={row.get('importerCount', 0)}"
        )
        for row in rows[:5]
    ]


def source_pattern_lines(report: dict[str, Any] | None) -> list[str]:
    """Render configurable source-pattern scan results."""

    if not report:
        return []
    lines = [
        "Source Patterns",
        f"- policy: {report.get('policyId', '') or '(unnamed)'}",
        f"- patterns: {report.get('patternCount', 0)}",
        source_pattern_count_line(report),
    ]
    lines.extend(source_pattern_diagnostic_lines(report.get("diagnostics", [])))
    lines.extend(source_pattern_summary_lines(report.get("patternSummary", [])))
    lines.extend(source_pattern_match_lines(report.get("matches", [])))
    return [*lines, ""]


def source_pattern_count_line(report: dict[str, Any]) -> str:
    """Render total and reported source-pattern match counts."""

    total = int(report.get("matchCount", 0))
    reported = int(report.get("reportedMatchCount", total))
    if reported != total:
        return f"- matches: {total} (reported {reported})"
    return f"- matches: {total}"


def source_pattern_diagnostic_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render invalid source-pattern policy rows."""

    return [
        f"- policy diagnostic {row.get('subject', '')}: {row.get('message', '')}"
        for row in rows[:5]
    ]


def source_pattern_summary_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render per-pattern source scan counts."""

    if not rows:
        return []
    return [
        (
            f"- pattern {row['patternId']}: {row['matchCount']} "
            f"kind={row['kind']} severity={row['severity']}"
        )
        for row in rows[:5]
    ]


def source_pattern_match_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render first source-pattern matches with source locations."""

    if not rows:
        return []
    return [
        (
            f"- {row['path']}:{row['line']} {row['patternId']} "
            f"generated={row.get('generated', False)}"
        )
        for row in rows[:5]
    ]


def module_dag_detail_lines(dag: dict[str, Any]) -> list[str]:
    """Render grouped module-DAG detail sections."""

    lines: list[str] = []
    lines.extend(module_fan_lines("Top Module Fan-In", dag.get("top_fan_in", []), "fan_in"))
    lines.extend(module_fan_lines("Top Module Fan-Out", dag.get("top_fan_out", []), "fan_out"))
    lines.extend(
        module_fan_lines(
            "Top Facade/Barrel Module Fan-Out",
            dag.get("top_facade_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Implementation Module Fan-Out",
            dag.get("top_implementation_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Handwritten Module Fan-In",
            dag.get("top_handwritten_fan_in", []),
            "fan_in",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Handwritten Module Fan-Out",
            dag.get("top_handwritten_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(large_module_lines(dag.get("top_large_handwritten_modules", [])))
    lines.extend(module_name_smell_lines(dag))
    lines.extend(generated_family_lines(dag.get("generated_family_summary", [])))
    lines.extend(duplicate_import_lines(dag.get("duplicate_imports", [])))
    lines.extend(duplicate_family_lines(dag.get("duplicate_import_family_summary", [])))
    lines.extend(facade_subtype_lines(dag))
    lines.extend(missing_internal_import_lines(dag.get("missing_internal_imports", [])))
    lines.extend(lexical_marker_lines(dag))
    lines.extend(root_import_closure_lines(dag.get("root_direct_import_closures", [])))
    lines.extend(named_module_lines("Facade Modules", dag.get("facade_modules", [])))
    lines.extend(unreachable_module_lines(dag))
    return lines


def large_module_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render largest non-generated source files."""

    visible = [row for row in rows if row.get("lineCount", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Largest Handwritten Modules"]
    lines.extend(f"- {row['module']}: {row['lineCount']} lines" for row in visible)
    return [*lines, ""]


def module_name_smell_lines(dag: dict[str, Any]) -> list[str]:
    """Render module-name pressure summaries and samples."""

    summary = dag.get("module_name_smell_summary", {})
    rows = dag.get("module_name_smells", [])
    if not summary and not rows:
        return []
    lines = ["Module Naming Smells"]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items()))
    lines.extend(module_name_smell_line(row) for row in rows[:5])
    return [*lines, ""]


def module_name_smell_line(row: dict[str, Any]) -> str:
    """Render one module naming-smell row."""

    reasons = ",".join(row.get("reasonKinds", [])[:4])
    action = row.get("suggestedAction", "review module naming")
    return (
        f"- {row['module']}: generated={row.get('generated', False)} "
        f"reasons={reasons}; {action}"
    )


def generated_family_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render generated families even when no duplicate imports exist."""

    if not rows:
        return []
    lines = ["Generated Families"]
    lines.extend(generated_family_line(row) for row in rows[:5])
    return [*lines, ""]


def generated_family_line(row: dict[str, Any]) -> str:
    """Render one generated-family summary row."""

    reasons = row.get("reasonSummary", {})
    reason_text = ",".join(
        f"{kind}={count}"
        for kind, count in sorted(reasons.items())[:4]
    )
    suffix = f" reasons={reason_text}" if reason_text else ""
    return (
        f"- {row.get('generatorFamily') or '(generated)'}: "
        f"{row['moduleCount']} modules maxDepth={row.get('maxPathDepth', 0)}{suffix}"
    )


def duplicate_import_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render duplicate import targets with compact line evidence."""

    if not rows:
        return []
    lines = ["Duplicate Imports"]
    lines.extend(duplicate_import_line(row) for row in rows[:5])
    return [*lines, ""]


def duplicate_import_line(row: dict[str, Any]) -> str:
    """Render one duplicate import row."""

    lines = row.get("lines", [])
    line_suffix = f" lines={','.join(str(line) for line in lines[:5])}" if lines else ""
    action = row.get("suggestedAction", "deduplicate the import target")
    return f"- {row['module']} -> {row['target']}: {row['count']}{line_suffix}; {action}"


def duplicate_family_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render duplicate imports grouped by generated family and target."""

    if not rows:
        return []
    lines = ["Duplicate Import Families"]
    lines.extend(
        (
            f"- {row.get('generatorFamily') or '(handwritten)'} -> {row['target']}: "
            f"{row['duplicateModuleCount']} modules generated={row.get('generated', False)}"
        )
        for row in rows[:5]
    )
    return [*lines, ""]


def facade_subtype_lines(dag: dict[str, Any]) -> list[str]:
    """Render facade subtype counts and top facade-like modules."""

    summary = dag.get("facade_subtype_summary", {})
    rows = dag.get("top_facade_like_modules", [])
    if not summary and not rows:
        return []
    lines = ["Facade Subtypes"]
    lines.extend(f"- {name}: {count}" for name, count in sorted(summary.items()))
    lines.extend(
        f"- {row['module']}: {row['subtype']} imports={row['fan_out']}"
        for row in rows[:5]
    )
    return [*lines, ""]


def missing_internal_import_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render missing internal import targets."""

    if not rows:
        return []
    lines = ["Missing Internal Import Targets"]
    lines.extend(
        f"- {row['sourcePath']}:{row.get('line', '')} imports {row['targetModule']}"
        for row in rows[:5]
    )
    return [*lines, ""]


def lexical_marker_lines(dag: dict[str, Any]) -> list[str]:
    """Render lexical marker summary and samples."""

    summary = dag.get("lexical_marker_summary", {})
    rows = dag.get("lexical_markers", [])
    lines = ["Lexical Markers"]
    if not summary:
        return [*lines, "- none", ""]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items()))
    lines.extend(
        f"- {row['path']}:{row['line']} {row['kind']}"
        for row in rows[:5]
    )
    return [*lines, ""]


def module_fan_lines(
    title: str,
    rows: list[dict[str, Any]],
    metric: str,
) -> list[str]:
    """Render module graph fan-in or fan-out rows."""

    visible = [row for row in rows if row.get(metric, 0) > 0][:5]
    if not visible:
        return []
    lines = [title]
    lines.extend(f"- {row['module']}: {row[metric]}" for row in visible)
    return [*lines, ""]


def named_module_lines(title: str, modules: list[str]) -> list[str]:
    """Render a named module list section."""

    if not modules:
        return []
    return [title, *[f"- {module}" for module in modules[:5]], ""]


def root_import_closure_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render direct root-import closure sizes."""

    visible = [row for row in rows if row.get("reachable_module_count", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Root Direct Import Closures"]
    lines.extend(
        f"- {row['root']} -> {row['direct_import']}: {row['reachable_module_count']}"
        for row in visible
    )
    return [*lines, ""]


def unreachable_module_lines(dag: dict[str, Any]) -> list[str]:
    """Render modules outside chosen-root reachability, if any."""

    count = int(dag.get("source_modules_not_reachable_from_chosen_roots_count", 0))
    modules = dag.get("source_modules_not_reachable_from_chosen_roots", [])
    if count == 0:
        return []
    return [
        "Modules Not Reachable From Chosen Roots",
        f"- count: {count}",
        *[f"- {module}" for module in modules[:5]],
        "",
    ]


def finding_lines(findings: list[dict[str, Any]]) -> list[str]:
    """Render concise root-focused findings."""

    visible = visible_findings(findings)
    if not visible:
        return []
    lines = ["Findings"]
    lines.extend(finding_line(finding) for finding in visible)
    return [*lines, ""]


def visible_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep detailed policy rows in JSON while avoiding noisy text output."""

    return [
        finding
        for finding in findings
        if finding.get("kind") not in POLICY_DETAIL_FINDING_KINDS
    ]


def finding_line(finding: dict[str, Any]) -> str:
    """Render one finding in a stable compact form."""

    return (
        f"- [{finding['severity']}] {finding['kind']} "
        f"{finding['subject']}: {finding['message']}"
        f"{policy_context_suffix(finding)}{baseline_suffix(finding)}"
    )


def policy_context_suffix(finding: dict[str, Any]) -> str:
    """Render optional direct-policy triage context."""

    if "policyContext" not in finding:
        return ""
    action = finding.get("suggestedAction", "")
    action_text = f"; {action}" if action else ""
    return f" ({finding['policyContext']} triage={finding.get('triageSeverity', '')}{action_text})"


def baseline_suffix(finding: dict[str, Any]) -> str:
    """Render optional metric calibration for one finding."""

    baseline = finding.get("baseline")
    if not baseline:
        return ""
    return (
        f" ({baseline['metric']} pctl={baseline['percentile']} "
        f"rank={baseline['rank_desc']}/{baseline['population']})"
    )


def quality_baseline_lines(baseline: dict[str, Any] | None) -> list[str]:
    """Render compact project-local metric baselines."""

    if not baseline:
        return []
    rows = [
        quality_metric_line(name, summary)
        for name, summary in sorted(baseline.get("metrics", {}).items())
        if summary.get("count", 0) > 0
    ]
    if not rows:
        return []
    return ["Quality Baseline", *rows, ""]


def quality_metric_line(name: str, summary: dict[str, Any]) -> str:
    """Render one metric baseline summary without listing raw values."""

    return (
        f"- {name}: count={summary['count']} min={summary['min']} "
        f"median={summary['median']} p90={summary['p90']} "
        f"p95={summary['p95']} p99={summary['p99']} max={summary['max']}"
    )


def packet_evidence_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render packet evidence completeness summaries."""

    if not rows:
        return []
    lines = ["Packet Evidence"]
    lines.extend(packet_evidence_line(row) for row in rows)
    return [*lines, ""]


def packet_evidence_line(row: dict[str, Any]) -> str:
    """Render one packet evidence row."""

    suffix = packet_profile_suffix(row)
    return f"- {row['packet_dir']}: {row['status']} score={row['score']}/{row['max_score']}{suffix}"


def packet_profile_suffix(row: dict[str, Any]) -> str:
    """Render optional evidence-profile status."""

    if "profile" not in row:
        return ""
    return f" profile={row['profile']} profile_status={row['profile_status']}"


def review_region_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render additive review-region summaries."""

    if not rows:
        return []
    lines = ["Review Regions"]
    lines.extend(review_region_line(row) for row in rows)
    return [*lines, ""]


def review_region_line(row: dict[str, Any]) -> str:
    """Render one review-region row."""

    return f"- {row['kind']}: {row['title']} (signals={row['signal_count']})"


def declaration_graph_lines(summary: dict[str, Any] | None) -> list[str]:
    """Render declaration graph summary when declaration IR was available."""

    if summary is None:
        return []
    lines = [
        "Declaration Graph",
        f"- declarations: {summary['declaration_count']}",
        f"- edges: {summary['edge_count']}",
        f"- unresolved references: {summary['unresolved_reference_count']}",
        "",
    ]
    lines.extend(declaration_evidence_lines(summary.get("declarations", [])))
    lines.extend(declaration_fan_lines("Top Declaration Fan-In", summary.get("top_fan_in", []), "fan_in"))
    lines.extend(
        declaration_fan_lines("Top Declaration Fan-Out", summary.get("top_fan_out", []), "fan_out")
    )
    lines.extend(declaration_family_lines(summary.get("declaration_name_families", [])))
    lines.extend(
        proof_family_similarity_lines(summary.get("proof_family_similarity_candidates", []))
    )
    lines.extend(unresolved_reference_class_lines(summary.get("unresolved_reference_classes", [])))
    lines.extend(unresolved_reference_lines(summary.get("top_unresolved_references", [])))
    lines.extend(
        actionable_unresolved_reference_lines(
            summary.get("top_actionable_unresolved_references", [])
        )
    )
    return lines


def declaration_evidence_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render declaration source-evidence coverage without proof overclaims."""

    if not rows:
        return []
    confidences = confidence_counts(rows)
    lines = [
        "Declaration Evidence",
        f"- rows: {len(rows)}",
        f"- source ranges: {count_present(rows, 'sourceRange')}",
        f"- content hashes: {count_present(rows, 'contentHash')}",
    ]
    lines.extend(f"- confidence {name}: {count}" for name, count in sorted(confidences.items()))
    lines.append("- trust: source evidence is attachment confidence, not proof truth")
    return [*lines, ""]


def confidence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count declaration evidence rows by explicit confidence label."""

    counts: dict[str, int] = {}
    for row in rows:
        confidence = str(row.get("confidence", "unspecified"))
        counts[confidence] = counts.get(confidence, 0) + 1
    return counts


def count_present(rows: list[dict[str, Any]], key: str) -> int:
    """Count rows that expose one optional evidence field."""

    return sum(1 for row in rows if row.get(key) is not None)


def declaration_fan_lines(
    title: str,
    rows: list[dict[str, Any]],
    metric: str,
) -> list[str]:
    """Render declaration graph fan-in or fan-out hotspots."""

    visible = [row for row in rows if row.get(metric, 0) > 0][:5]
    if not visible:
        return []
    lines = [title]
    lines.extend(f"- {row['declaration']}: {row[metric]}" for row in visible)
    return [*lines, ""]


def unresolved_reference_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render common unresolved reference candidates."""

    visible = [row for row in rows if row.get("count", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Top Unresolved References"]
    lines.extend(unresolved_reference_line(row) for row in visible)
    return [*lines, ""]


def unresolved_reference_class_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render unresolved reference occurrence counts by class."""

    if not rows:
        return []
    lines = ["Unresolved Reference Classes"]
    lines.extend(f"- {row['classification']}: {row['count']}" for row in rows[:6])
    return [*lines, ""]


def declaration_family_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render declaration name family groups."""

    visible = [row for row in rows if row.get("count", 0) > 1][:5]
    if not visible:
        return []
    lines = ["Declaration Name Families"]
    lines.extend(f"- {row['suffix']}: {row['count']}" for row in visible)
    return [*lines, ""]


def proof_family_similarity_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render deterministic proof-family similarity candidates."""

    if not rows:
        return []
    lines = ["Proof Family Similarity Candidates"]
    lines.extend(proof_family_similarity_line(row) for row in rows[:5])
    return [*lines, ""]


def proof_family_similarity_line(row: dict[str, Any]) -> str:
    """Render one proof-family similarity row without clone claims."""

    pair = " | ".join(row.get("best_pair", []))
    return (
        f"- {row['suffix']}: similar proof-family candidate "
        f"score={row['similarity_score']} pair={pair}"
    )


def unresolved_reference_line(row: dict[str, Any]) -> str:
    """Render one unresolved reference row with an optional classification."""

    classification = row.get("classification")
    suffix = f" ({classification})" if classification else ""
    return f"- {row['candidate']}: {row['count']}{suffix}"


def actionable_unresolved_reference_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render unresolved candidates worth human follow-up."""

    visible = [row for row in rows if row.get("count", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Top Actionable Unresolved References"]
    lines.extend(f"- {row['candidate']}: {row['count']}" for row in visible)
    return [*lines, ""]


def timing_lines(timings: dict[str, dict[str, Any]]) -> list[str]:
    """Render phase timing status without depending on exact durations."""

    if not timings:
        return []
    lines = ["Pipeline Phases"]
    for name, timing in timings.items():
        lines.append(f"- {name}: {timing['status']} ({timing['elapsed_seconds']:.6f}s)")
    return [*lines, ""]


def write_report(
    payload: dict[str, Any],
    *,
    output_json: str | None,
    output_text: str | None,
) -> None:
    """Write or print JSON and text report forms."""

    text = render_text(payload)
    if output_json:
        write_text(Path(output_json), json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    if output_text:
        write_text(Path(output_text), text)
    else:
        print(text)


def write_text(path: Path, content: str) -> None:
    """Create parent directories and write UTF-8 report text."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
