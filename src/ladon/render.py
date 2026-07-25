"""Stable JSON/text rendering facade for Ladon's clean-core report.

Renderers consume already-computed report data. They do not inspect target
repositories or run analysis. Cohesive section renderers live in neighboring
modules while this module preserves the established import surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ladon.declaration_surface_render import (
    declaration_surface_lines,
    declaration_trust_lines,
)
from ladon.render_declarations import (
    actionable_unresolved_reference_lines,
    confidence_counts,
    count_present,
    declaration_evidence_lines,
    declaration_family_lines,
    declaration_fan_lines,
    declaration_graph_lines,
    proof_family_similarity_line,
    proof_family_similarity_lines,
    unresolved_reference_class_lines,
    unresolved_reference_line,
    unresolved_reference_lines,
)
from ladon.render_module_dag import (
    _audit_command_line,
    _audit_rows,
    _has_audit_summary,
    _resource_directive_line,
    audit_surface_lines,
    duplicate_family_lines,
    duplicate_import_line,
    duplicate_import_lines,
    facade_subtype_lines,
    fan_population_suffix,
    generated_family_line,
    generated_family_lines,
    large_module_lines,
    lexical_marker_lines,
    missing_internal_import_lines,
    module_dag_detail_lines,
    module_fan_lines,
    module_name_smell_line,
    module_name_smell_lines,
    named_module_lines,
    population_lines,
    root_import_closure_lines,
    scope_lines,
    unreachable_module_lines,
)
from ladon.render_review_sections import (
    POLICY_DETAIL_FINDING_KINDS,
    architecture_context_lines,
    architecture_import_sample,
    architecture_offending_file_line,
    architecture_offending_file_lines,
    architecture_pair_lines,
    architecture_policy_lines,
    architecture_shared_dependency_lines,
    baseline_suffix,
    finding_line,
    finding_lines,
    packet_evidence_line,
    packet_evidence_lines,
    packet_profile_suffix,
    policy_context_suffix,
    quality_baseline_lines,
    quality_metric_line,
    review_region_line,
    review_region_lines,
    source_pattern_count_line,
    source_pattern_diagnostic_lines,
    source_pattern_lines,
    source_pattern_match_lines,
    source_pattern_summary_lines,
    visible_findings,
    warning_lines,
)
from ladon.report_contract import SECTION_PHASES, sorted_diagnostics
from ladon.report_v2 import ReportV2, coerce_report_v2, serialize_report_bytes
from ladon.review_intelligence_render import (
    import_diet_lines,
    module_readiness_lines,
    proof_xray_lines,
    refactoring_prescription_lines,
)


def render_text(payload: dict[str, Any] | ReportV2) -> str:
    """Render a concise human-readable projection of the canonical model."""

    payload = _text_report_payload(coerce_report_v2(payload))
    metadata = payload["metadata"]
    dag = payload["module_dag"]
    lines = [
        "Ladon Report",
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
    lines.extend(module_readiness_lines(payload.get("module_readiness")))
    lines.extend(architecture_policy_lines(payload.get("architecture_policy")))
    lines.extend(source_pattern_lines(payload.get("source_patterns")))
    lines.extend(import_diet_lines(payload.get("import_diet")))
    lines.extend(proof_xray_lines(payload.get("proof_xray")))
    lines.extend(
        refactoring_prescription_lines(
            payload.get("refactoring_prescriptions")
        )
    )
    lines.extend(finding_lines(payload.get("findings", [])))
    lines.extend(quality_baseline_lines(payload.get("quality_baseline")))
    lines.extend(packet_evidence_lines(payload.get("packet_evidence", [])))
    lines.extend(review_region_lines(payload.get("review_regions", [])))
    lines.extend(declaration_graph_lines(payload.get("declaration_graph")))
    lines.extend(timing_lines(payload.get("pipeline", {}).get("timings", {})))
    lines.extend(scope_lines(dag))
    lines.extend(population_lines(dag))
    lines.extend(audit_surface_lines(dag))
    lines.extend(module_dag_detail_lines(dag))
    return "\n".join(lines).rstrip() + "\n"


def _text_report_payload(report: ReportV2) -> dict[str, Any]:
    """Expose only fields consumed by text rendering without copying sections."""

    payload: dict[str, Any] = {
        "metadata": report.metadata.to_dict(),
        "warnings": list(report.warnings),
        "findings": [
            row.to_dict()
            for row in sorted(
                report.findings,
                key=lambda finding: (
                    finding.kind,
                    finding.subject,
                    finding.identifier,
                ),
            )
        ],
        "pipeline": {
            "timings": {
                name: _text_phase_timing(report.phases[name])
                for name in sorted(report.phases)
            }
        },
    }
    for section, phase_name in SECTION_PHASES.items():
        data = report.phases[phase_name].data
        if section == "module_dag":
            payload[section] = data if isinstance(data, dict) else {}
        elif data is not None:
            payload[section] = data
    return payload


def _text_phase_timing(phase) -> dict[str, Any]:
    """Return phase state needed by compact text, excluding owner data."""

    return {
        "name": phase.name,
        "status": phase.status,
        "required": phase.required,
        "elapsed_seconds": phase.elapsed_seconds,
        "counters": dict(sorted(phase.counters.items())),
        "reason": phase.reason,
        "diagnostics": [
            row.to_dict() for row in sorted_diagnostics(phase.diagnostics)
        ],
    }


def timing_lines(timings: dict[str, dict[str, Any]]) -> list[str]:
    """Render phase timing status without depending on exact durations."""

    if not timings:
        return []
    lines = ["Pipeline Phases"]
    for name, timing in timings.items():
        lines.extend(timing_row_lines(name, timing))
    return [*lines, ""]


def timing_row_lines(name: str, timing: dict[str, Any]) -> list[str]:
    """Render one phase and bounded retained-state diagnostics."""

    line = f"- {name}: {timing['status']} ({timing['elapsed_seconds']:.6f}s)"
    reason = timing.get("reason")
    if reason:
        line += f" — {reason}"
    lines = [line]
    if timing.get("status") == "complete":
        return lines
    counters = timing.get("counters", {})
    if isinstance(counters, dict) and counters:
        values = ", ".join(
            f"{key}={value}" for key, value in sorted(counters.items())
        )
        lines.append(f"  retained counters: {values}")
    diagnostics = timing.get("diagnostics", [])
    lines.extend(
        timing_diagnostic_line(row)
        for row in diagnostics[:3]
        if isinstance(row, dict)
    )
    omitted = max(0, len(diagnostics) - 3)
    if omitted:
        lines.append(f"  diagnostics omitted: {omitted}")
    return lines


def timing_diagnostic_line(row: dict[str, Any]) -> str:
    """Render one structured phase diagnostic with its affected subject."""

    subject = f" subject={row['subject']}" if row.get("subject") else ""
    return (
        f"  diagnostic {row.get('id', 'unknown')}{subject}: "
        f"{row.get('message', '')}"
    )


def write_report(
    payload: dict[str, Any] | ReportV2,
    *,
    output_json: str | None,
    output_text: str | None,
) -> None:
    """Write or print JSON and text report forms."""

    canonical = coerce_report_v2(payload)
    text = render_text(canonical)
    content = serialize_report_bytes(canonical).content.decode("utf-8")
    if output_json:
        write_text(Path(output_json), content)
    else:
        print(content, end="")
    if output_text:
        write_text(Path(output_text), text)
    else:
        print(text)


def write_text(path: Path, content: str) -> None:
    """Create parent directories and write UTF-8 report text."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
