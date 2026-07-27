"""Stable facade and phase orchestration for calibrated analysis.

Module evidence, lexical audits, module populations, and declaration
populations are independent implementation boundaries.  This module preserves
the established import surface and keeps phase ordering explicit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ladon.analysis.architecture_registrations import (
    attach_architecture_producer_registrations,
)
from ladon.analysis.audit_roles import finalize_audit_roles
from ladon.analysis.declaration_graph import summarize_declaration_graph
from ladon.analysis.findings import summarize_findings
from ladon.analysis.quality_baseline import summarize_quality_baseline
from ladon.analysis.refactoring_prescriptions import (
    summarize_refactoring_prescriptions,
)
from ladon.analysis.review_regions import summarize_review_regions
from ladon.analysis.witness_packet import summarize_packet_evidence
from ladon.extraction import ModuleDiscovery
from ladon.ir import LeanDeclaration, LeanModule
from ladon.pipeline_audit_calibration import (
    attach_audit_query_results,
    attach_audit_surfaces,
    enrich_audit_and_declaration_populations,
    enrich_audit_command,
)
from ladon.pipeline_declaration_calibration import (
    attach_declaration_populations,
    calibrated_declaration_ranking,
    calibrated_declaration_row,
    declaration_population,
    normalized_declaration_edges,
    reverse_declaration_relationships,
)
from ladon.pipeline_extraction import (
    analysis_module_roots,
    declaration_roots_for_modules,
    reference_inventory_names,
)
from ladon.pipeline_integrity import attach_integrity_surfaces
from ladon.pipeline_inspection_navigation import (
    attach_inspection_navigation,
)
from ladon.pipeline_models import RunContext
from ladon.pipeline_module_evidence import (
    attach_boundary_membership_evidence,
    boundary_membership_rows,
    boundary_targets,
    discovery_phase_reason,
    rewrite_boundary_membership_refs,
    rewrite_inventory_reference,
    root_view_configuration,
    scope_source_fingerprint,
    selected_import_coverage,
    selected_module_dag,
    source_index_summary,
)
from ladon.pipeline_population_calibration import (
    attach_audit_populations,
    attach_module_populations,
    legacy_population_field,
    module_population_candidate,
    target_owned_fan_in_rows,
    target_owned_fan_out_rows,
    target_owned_large_module_rows,
    target_source_roots,
)
from ladon.pipeline_snapshot import (
    capture_registered_directory,
    read_registered_text,
)


def run_module_dag_phase(
    context: RunContext,
    modules: Mapping[str, LeanModule],
    discovery: ModuleDiscovery,
) -> dict[str, Any]:
    """Summarize the module DAG for the selected analysis root."""

    with context.phase("module_dag") as counters:
        plan = context.scope_plan
        dag = selected_module_dag(context, modules, discovery)
        if plan is not None:
            dag["analysis_scope"] = plan.to_payload()
        dag["source_index"] = source_index_summary(context, len(modules))
        attach_boundary_membership_evidence(dag, context.source_index)
        attach_inspection_navigation(dag, modules, context.source_index)
        attach_audit_surfaces(context, dag, modules)
        finalize_audit_roles(dag)
        attach_module_populations(context, dag, modules)
        attach_integrity_surfaces(context, dag, discovery)
        dag["scope"] = plan.scope_kind if plan is not None else "inventory"
        dag["method"] = "selected_module_import_dag"
        counters["edges"] = int(dag["edge_count"])
        if context.source_index_status == "partial":
            reason = discovery_phase_reason(context)
            dag["completeness"] = {
                "status": "partial",
                "reason": reason,
                "metricsSuppressed": False,
                "metricsPopulation": "retained_readable_modules",
            }
            context.mark_phase_partial("module_dag", reason)
    return dag


def run_declaration_graph_phase(
    context: RunContext,
    discovery: ModuleDiscovery,
    declarations: Mapping[str, LeanDeclaration],
    modules: Mapping[str, LeanModule],
) -> dict[str, Any] | None:
    """Summarize declaration evidence when the backend provided declarations."""

    if declarations:
        with context.phase("declaration_graph") as counters:
            declaration_graph = summarize_declaration_graph(
                declarations,
                chosen_roots=declaration_roots_for_modules(
                    analysis_module_roots(context, discovery),
                    declarations,
                ),
                known_reference_names=reference_inventory_names(modules),
            )
            counters["declarations"] = int(declaration_graph["declaration_count"])
            counters["edges"] = int(declaration_graph["edge_count"])
            return declaration_graph
    context.record_skipped("declaration_graph", "no declaration IR available")
    return None


def run_quality_baseline_phase(
    context: RunContext,
    dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> dict[str, Any]:
    """Summarize baseline quality metrics."""

    with context.phase("quality_baseline") as counters:
        quality_baseline = summarize_quality_baseline(
            dag,
            declaration_graph,
        )
        counters["metrics"] = len(quality_baseline["metrics"])
        return quality_baseline


def run_findings_phase(
    context: RunContext,
    dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    quality_baseline: dict[str, Any],
    module_readiness: dict[str, Any] | None,
    architecture_policy: dict[str, Any] | None,
    source_patterns: dict[str, Any] | None,
    import_diet: dict[str, Any] | None,
    proof_xray: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build the combined findings list from all completed analyses."""

    with context.phase("findings") as counters:
        findings = summarize_findings(
            dag,
            declaration_graph,
            quality_baseline,
        )
        for report in (
            module_readiness,
            architecture_policy,
            source_patterns,
            import_diet,
            proof_xray,
        ):
            if report is not None:
                findings.extend(report["findings"])
        attach_architecture_producer_registrations(
            context,
            dag,
            findings,
            declaration_graph,
        )
        counters["findings"] = len(findings)
        return findings


def run_refactoring_prescription_phase(
    context: RunContext,
    dag: dict[str, Any],
    findings: list[dict[str, Any]],
    architecture_policy: dict[str, Any] | None,
    import_diet: dict[str, Any] | None,
    proof_xray: dict[str, Any] | None,
) -> dict[str, Any]:
    """Create review-prescription rows and append their findings."""

    with context.phase("refactoring_prescriptions") as counters:
        refactoring_prescriptions = summarize_refactoring_prescriptions(
            module_dag=dag,
            findings=findings,
            architecture_policy=architecture_policy,
            import_diet=import_diet,
            proof_xray=proof_xray,
        )
        findings.extend(refactoring_prescriptions["findings"])
        context.set_phase_counter("findings", "findings", len(findings))
        counters["prescriptions"] = len(refactoring_prescriptions["rows"])
        return refactoring_prescriptions


def run_packet_evidence_phase(
    context: RunContext,
) -> list[dict[str, Any]]:
    """Summarize optional OpenSpec/proof packet evidence directories."""

    packet_dirs = (
        context.captured_packet_dirs
        if context.captured_packet_dirs is not None
        else context.packet_dirs
    )
    if packet_dirs:
        with context.phase("packet_evidence") as counters:
            packet_evidence = [
                _summarize_registered_packet(
                    context,
                    packet_dir,
                    index=index,
                )
                for index, packet_dir in enumerate(packet_dirs)
            ]
            counters["packet_dirs"] = len(packet_evidence)
            return packet_evidence
    context.record_skipped(
        "packet_evidence",
        "no packet directories requested",
    )
    return []


def _summarize_registered_packet(
    context: RunContext,
    packet_dir: Path,
    *,
    index: int,
) -> dict[str, Any]:
    """Summarize one packet from a captured inventory and registered text."""

    collection_refs = (
        "report.packet_evidence",
        "report.review_regions",
    )
    inventory = capture_registered_directory(
        context,
        packet_dir,
        namespace=f"packet-{index}",
        collection_refs=collection_refs,
    )
    return summarize_packet_evidence(
        packet_dir,
        profile=(
            context.captured_packet_profile
            if context.captured_packet_profile is not None
            else context.packet_profile
        ),
        captured_files=list(inventory.files),
        packet_exists=inventory.exists,
        text_reader=lambda path: read_registered_text(
            context,
            path,
            kind="evidence",
            collection_refs=collection_refs,
            namespace="packet-evidence",
            errors="ignore",
            register_unreadable=True,
        ),
    )


def run_review_regions_phase(
    context: RunContext,
    dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
    findings: list[dict[str, Any]],
    packet_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize reviewer routing regions."""

    with context.phase("review_regions") as counters:
        review_regions = summarize_review_regions(
            dag,
            declaration_graph,
            findings,
            packet_evidence,
        )
        counters["regions"] = len(review_regions)
        return review_regions


__all__ = [
    "attach_audit_populations",
    "attach_audit_query_results",
    "attach_audit_surfaces",
    "attach_boundary_membership_evidence",
    "attach_declaration_populations",
    "attach_module_populations",
    "boundary_membership_rows",
    "boundary_targets",
    "calibrated_declaration_ranking",
    "calibrated_declaration_row",
    "declaration_population",
    "discovery_phase_reason",
    "enrich_audit_and_declaration_populations",
    "enrich_audit_command",
    "legacy_population_field",
    "module_population_candidate",
    "normalized_declaration_edges",
    "reverse_declaration_relationships",
    "rewrite_boundary_membership_refs",
    "rewrite_inventory_reference",
    "root_view_configuration",
    "run_declaration_graph_phase",
    "run_findings_phase",
    "run_module_dag_phase",
    "run_packet_evidence_phase",
    "run_quality_baseline_phase",
    "run_refactoring_prescription_phase",
    "run_review_regions_phase",
    "scope_source_fingerprint",
    "selected_import_coverage",
    "selected_module_dag",
    "source_index_summary",
    "target_owned_fan_in_rows",
    "target_owned_fan_out_rows",
    "target_owned_large_module_rows",
    "target_source_roots",
]
