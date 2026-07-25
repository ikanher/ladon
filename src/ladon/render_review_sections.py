"""Text rendering for policy, finding, evidence, and review sections."""

from __future__ import annotations

from typing import Any


POLICY_DETAIL_FINDING_KINDS = {
    "architecture_policy.direct_forbidden_import",
    "architecture_policy.transitive_forbidden_import",
    "architecture_policy.shared_dependency_candidate",
    "module_readiness.malformed_witness",
    "module_readiness.public_facade_pressure",
    "module_readiness.implementation_public_pressure",
    "module_readiness.generated_public_aggregation",
    "module_readiness.namespace_module_drift",
    "module_readiness.module_system_witness",
    "import_diet.malformed_witness",
    "import_diet.redundant_import_candidate",
    "import_diet.stale_import_diet_witness",
    "proof_xray.malformed_witness",
    "proof_xray.weak_authority_metadata",
    "proof_xray.automation_hotspot",
    "proof_xray.dependency_context",
    "proof_xray.trust_footprint",
    "refactoring_prescription.extract_common_lower_layer",
    "refactoring_prescription.move_bridge_to_neutral_namespace",
    "refactoring_prescription.declare_explicit_bridge_policy",
    "refactoring_prescription.split_large_owner",
    "refactoring_prescription.promote_public_facade",
    "refactoring_prescription.demote_implementation_import",
    "refactoring_prescription.clean_generator_output",
    "refactoring_prescription.move_generated_parameters_to_manifest",
    "refactoring_prescription.run_import_diet",
    "refactoring_prescription.add_proof_surface_witness_evidence",
    "source_pattern.invalid_policy",
    "source_pattern.match",
}


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


def finding_lines(findings: list[dict[str, Any]]) -> list[str]:
    """Render concise root-focused findings."""

    visible = visible_findings(findings)
    if not findings:
        return []
    lines = [
        "Findings",
        f"- selected: {len(findings)}",
        f"- displayed: {len(visible)}",
        f"- omitted: {len(findings) - len(visible)}",
    ]
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
        f" (id={finding['id']} evidence={finding['evidence_count']} "
        f"authority={finding['authority']})"
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
