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
        "",
    ]
    lines.extend(warning_lines(payload.get("warnings", [])))
    lines.extend(finding_lines(payload.get("findings", [])))
    lines.extend(quality_baseline_lines(payload.get("quality_baseline")))
    lines.extend(packet_evidence_lines(payload.get("packet_evidence", [])))
    lines.extend(declaration_graph_lines(payload.get("declaration_graph")))
    lines.extend(timing_lines(payload.get("pipeline", {}).get("timings", {})))
    lines.extend(module_dag_detail_lines(dag))
    return "\n".join(lines).rstrip() + "\n"


def warning_lines(warnings: list[str]) -> list[str]:
    """Render support-boundary warnings, if any."""

    if not warnings:
        return []
    return ["Warnings", *[f"- {warning}" for warning in warnings], ""]


def module_dag_detail_lines(dag: dict[str, Any]) -> list[str]:
    """Render grouped module-DAG detail sections."""

    lines: list[str] = []
    lines.extend(module_fan_lines("Top Module Fan-In", dag.get("top_fan_in", []), "fan_in"))
    lines.extend(module_fan_lines("Top Module Fan-Out", dag.get("top_fan_out", []), "fan_out"))
    lines.extend(root_import_closure_lines(dag.get("root_direct_import_closures", [])))
    lines.extend(named_module_lines("Facade Modules", dag.get("facade_modules", [])))
    lines.extend(unreachable_module_lines(dag))
    return lines


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

    if not findings:
        return []
    lines = ["Findings"]
    lines.extend(finding_line(finding) for finding in findings)
    return [*lines, ""]


def finding_line(finding: dict[str, Any]) -> str:
    """Render one finding in a stable compact form."""

    return (
        f"- [{finding['severity']}] {finding['kind']} "
        f"{finding['subject']}: {finding['message']}{baseline_suffix(finding)}"
    )


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

    return f"- {row['packet_dir']}: {row['status']} score={row['score']}/{row['max_score']}"


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
