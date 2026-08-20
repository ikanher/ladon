"""Human rendering for one already-materialized report-v3 projection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.render import (
    architecture_policy_lines,
    audit_surface_lines,
    declaration_graph_lines,
    finding_lines,
    import_diet_lines,
    module_dag_detail_lines,
    module_readiness_lines,
    packet_evidence_lines,
    population_lines,
    proof_xray_lines,
    quality_baseline_lines,
    refactoring_prescription_lines,
    report_root_header_lines,
    review_region_lines,
    scope_lines,
    source_pattern_lines,
    timing_lines,
    warning_lines,
)
from ladon.report_v3 import ReportV3

_DAG_SUMMARY_FIELDS = (
    "module_count",
    "edge_count",
    "acyclic",
    "topological_layer_count",
    "facade_module_count",
)


def render_report_v3_text(report: ReportV3) -> str:
    """Render text from the exact projected rows and coverage in ``report``."""

    payload = _mapping(report.payload)
    metadata = _mapping(payload.get("metadata"))
    sections = _mapping(payload.get("sections"))
    dag = _mapping(sections.get("module_dag"))
    lines = [
        "Ladon Report",
        f"Root: {metadata.get('repo_root', '')}",
        *report_root_header_lines(metadata, dag),
        f"Analysis fingerprint: {report.analysis_fingerprint}",
        f"Projection: {report.projection}",
        *_snapshot_lines(payload.get("snapshot")),
        "",
        *_module_dag_lines(dag, payload.get("coverage")),
    ]
    lines.extend(warning_lines(_string_rows(payload.get("warnings"))))
    lines.extend(module_readiness_lines(_optional_mapping(sections, "module_readiness")))
    lines.extend(architecture_policy_lines(_optional_mapping(sections, "architecture_policy")))
    lines.extend(source_pattern_lines(_optional_mapping(sections, "source_patterns")))
    lines.extend(import_diet_lines(_optional_mapping(sections, "import_diet")))
    lines.extend(proof_xray_lines(_optional_mapping(sections, "proof_xray")))
    lines.extend(
        refactoring_prescription_lines(
            _optional_mapping(sections, "refactoring_prescriptions")
        )
    )
    lines.extend(finding_lines(_mapping_rows(sections.get("findings"))))
    lines.extend(quality_baseline_lines(_optional_mapping(sections, "quality_baseline")))
    lines.extend(packet_evidence_lines(_mapping_rows(sections.get("packet_evidence"))))
    lines.extend(review_region_lines(_mapping_rows(sections.get("review_regions"))))
    lines.extend(declaration_graph_lines(_optional_mapping(sections, "declaration_graph")))
    lines.extend(
        timing_lines(
            dict(
                _mapping(
                    _mapping(payload.get("pipeline")).get("timings")
                )
            )
        )
    )
    if all(field in dag for field in _DAG_SUMMARY_FIELDS):
        lines.extend(scope_lines(dict(dag)))
        lines.extend(population_lines(dict(dag)))
        lines.extend(audit_surface_lines(dict(dag)))
        lines.extend(module_dag_detail_lines(dict(dag)))
    lines.extend(_coverage_lines(payload.get("coverage")))
    return "\n".join(lines).rstrip() + "\n"


def _snapshot_lines(raw: Any) -> list[str]:
    snapshot = _mapping(raw)
    if not snapshot:
        return []
    decision = _mapping(snapshot.get("decision"))
    return [
        f"Snapshot: {snapshot.get('identity', '')}",
        f"Source fingerprint: {snapshot.get('sourceIndexFingerprint', '')}",
        f"Snapshot state: {decision.get('status', 'unverified')}",
    ]


def _module_dag_lines(
    dag: Mapping[str, Any],
    raw_coverage: Any,
) -> list[str]:
    if all(field in dag for field in _DAG_SUMMARY_FIELDS):
        return [
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
    coverage = _coverage_collection(raw_coverage, "module_dag.modules")
    return [
        "Module DAG",
        (
            "- projected module rows: "
            f"{coverage.get('visible', 0)} visible, "
            f"{_count(coverage.get('total'))} total, "
            f"completeness={coverage.get('completeness', 'unavailable')}"
        ),
        "",
    ]


def _coverage_lines(raw: Any) -> list[str]:
    collections = _mapping(_mapping(raw).get("collections"))
    if not collections:
        return []
    lines = ["Collection Coverage"]
    for identity, value in sorted(collections.items()):
        row = _mapping(value)
        lines.append(
            f"- {identity}: visible={row.get('visible', 0)} "
            f"total={_count(row.get('total'))} "
            f"omitted={_count(row.get('omitted'))} "
            f"completeness={row.get('completeness', 'unavailable')} "
            f"authority={row.get('authority', 'unavailable')} "
            f"population={row.get('population', 'unavailable')} "
            f"scope={row.get('scope', 'unavailable')}"
        )
    return [*lines, ""]


def _coverage_collection(raw: Any, identity: str) -> Mapping[str, Any]:
    return _mapping(_mapping(_mapping(raw).get("collections")).get(identity))


def _optional_mapping(
    sections: Mapping[str, Any],
    name: str,
) -> dict[str, Any] | None:
    value = sections.get(name)
    return dict(value) if isinstance(value, Mapping) else None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _string_rows(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value]


def _count(value: Any) -> str:
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else "unknown"


__all__ = ["render_report_v3_text"]
