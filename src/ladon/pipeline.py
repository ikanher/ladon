"""Stable public facade and orchestration for Ladon's analysis pipeline.

The pipeline is the boundary between side effects and pure analysis. Cohesive
phase implementations live in neighboring modules; this facade preserves the
established ``ladon.pipeline`` import surface and execution order.
"""

from __future__ import annotations

from typing import Any

from ladon.extraction import ModuleDiscovery
from ladon.ir import LeanDeclaration, LeanModule
from ladon.pipeline_calibration import (
    attach_audit_surfaces,
    attach_declaration_populations,
    attach_module_populations,
    calibrated_declaration_ranking,
    calibrated_declaration_row,
    declaration_population,
    discovery_phase_reason,
    enrich_audit_and_declaration_populations,
    enrich_audit_command,
    module_population_candidate,
    normalized_declaration_edges,
    reverse_declaration_relationships,
    run_declaration_graph_phase,
    run_findings_phase,
    run_module_dag_phase,
    run_packet_evidence_phase,
    run_quality_baseline_phase,
    run_refactoring_prescription_phase,
    run_review_regions_phase,
    target_owned_fan_in_rows,
    target_source_roots,
)
from ladon.pipeline_extraction import (
    adapt_modules,
    add_index_counters,
    analysis_module_roots,
    coerce_extraction_bundle,
    count_declarations,
    declaration_name_variants,
    declaration_roots_for_modules,
    declarations_from_modules,
    default_lean_extractor,
    discovery_with_modules,
    finalize_discovery_phase,
    indexed_discovery,
    lean_extraction_phase_data,
    lean_partial_reason,
    merge_module_inventory,
    merge_module_row,
    reference_inventory_names,
    run_extraction_phases,
    run_lean_extractor,
    run_selected_extraction_backend,
    text_extraction_bundle,
)
from ladon.pipeline_models import (
    CORE_REQUIRED_PHASES,
    REQUIRED_PHASES,
    PhaseTiming,
    PipelineResult,
    RunContext,
    pipeline_result,
    progress_cache_counters,
    progress_completed,
    report_phase_data,
    require_core_report_phases,
)
from ladon.pipeline_optional import (
    ARCHITECTURE_POLICY_CANDIDATES,
    GENERATED_FAMILY_POLICY_CANDIDATES,
    SOURCE_PATTERN_POLICY_CANDIDATES,
    discover_architecture_policy_path,
    discover_source_pattern_policy_path,
    load_architecture_policy,
    load_json_object,
    load_source_pattern_policy,
    resolve_architecture_policy,
    resolve_generated_family_policy,
    resolve_optional_json,
    resolve_source_pattern_policy,
    run_architecture_policy_phase,
    run_import_diet_phase,
    run_module_readiness_phase,
    run_proof_xray_phase,
    run_source_pattern_phase,
    source_documents,
)
from ladon.pipeline_partial import (
    discovery_partial_result,
    incomplete_module_dag,
    partial_limit_result,
    record_limit_skips,
    resource_limit_reason,
    retained_limit_discovery,
    retained_limit_modules,
)
from ladon.progress import ResourceLimitExceeded


__all__ = [
    "ARCHITECTURE_POLICY_CANDIDATES",
    "CORE_REQUIRED_PHASES",
    "GENERATED_FAMILY_POLICY_CANDIDATES",
    "PhaseTiming",
    "PipelineResult",
    "REQUIRED_PHASES",
    "RunContext",
    "SOURCE_PATTERN_POLICY_CANDIDATES",
    "adapt_modules",
    "add_index_counters",
    "analysis_module_roots",
    "attach_audit_surfaces",
    "attach_declaration_populations",
    "attach_module_populations",
    "calibrated_declaration_ranking",
    "calibrated_declaration_row",
    "coerce_extraction_bundle",
    "count_declarations",
    "declaration_name_variants",
    "declaration_population",
    "declaration_roots_for_modules",
    "declarations_from_modules",
    "default_lean_extractor",
    "discover_architecture_policy_path",
    "discover_source_pattern_policy_path",
    "discovery_partial_result",
    "discovery_phase_reason",
    "discovery_with_modules",
    "enrich_audit_and_declaration_populations",
    "enrich_audit_command",
    "finalize_discovery_phase",
    "incomplete_module_dag",
    "indexed_discovery",
    "lean_extraction_phase_data",
    "lean_partial_reason",
    "load_architecture_policy",
    "load_json_object",
    "load_source_pattern_policy",
    "merge_module_inventory",
    "merge_module_row",
    "module_population_candidate",
    "normalized_declaration_edges",
    "partial_limit_result",
    "pipeline_result",
    "progress_cache_counters",
    "progress_completed",
    "record_limit_skips",
    "reference_inventory_names",
    "report_phase_data",
    "require_core_report_phases",
    "resolve_architecture_policy",
    "resolve_generated_family_policy",
    "resolve_optional_json",
    "resolve_source_pattern_policy",
    "resource_limit_reason",
    "retained_limit_discovery",
    "retained_limit_modules",
    "reverse_declaration_relationships",
    "run_architecture_policy_phase",
    "run_declaration_graph_phase",
    "run_extraction_phases",
    "run_findings_phase",
    "run_import_diet_phase",
    "run_lean_extractor",
    "run_module_dag_phase",
    "run_module_readiness_phase",
    "run_packet_evidence_phase",
    "run_pipeline",
    "run_proof_xray_phase",
    "run_quality_baseline_phase",
    "run_refactoring_prescription_phase",
    "run_review_regions_phase",
    "run_selected_extraction_backend",
    "run_source_pattern_phase",
    "source_documents",
    "target_owned_fan_in_rows",
    "target_source_roots",
    "text_extraction_bundle",
]


def run_pipeline(context: RunContext) -> PipelineResult:
    """Run the clean-core pipeline and return normalized results."""

    discovery: ModuleDiscovery | None = None
    modules: dict[str, LeanModule] = {}
    declarations: dict[str, LeanDeclaration] = {}
    dag: dict[str, Any] | None = None
    declaration_graph: dict[str, Any] | None = None
    module_readiness: dict[str, Any] | None = None
    architecture_policy: dict[str, Any] | None = None
    source_patterns: dict[str, Any] | None = None
    import_diet: dict[str, Any] | None = None
    proof_xray: dict[str, Any] | None = None
    quality_baseline: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = []
    refactoring_prescriptions: dict[str, Any] | None = None
    packet_evidence: list[dict[str, Any]] = []
    review_regions: list[dict[str, Any]] = []
    try:
        discovery, modules, declarations = run_extraction_phases(context)
        dag = run_module_dag_phase(context, modules, discovery)
        declaration_graph = run_declaration_graph_phase(
            context,
            discovery,
            declarations,
            modules,
        )
        enrich_audit_and_declaration_populations(dag, declaration_graph)
        module_readiness = run_module_readiness_phase(
            context,
            dag,
            declaration_graph,
        )
        architecture_policy = run_architecture_policy_phase(context, dag)
        source_patterns = run_source_pattern_phase(context, modules)
        import_diet = run_import_diet_phase(context, dag)
        proof_xray = run_proof_xray_phase(context)
        quality_baseline = run_quality_baseline_phase(
            context,
            dag,
            declaration_graph,
        )
        findings = run_findings_phase(
            context,
            dag,
            declaration_graph,
            quality_baseline,
            module_readiness,
            architecture_policy,
            source_patterns,
            import_diet,
            proof_xray,
        )
        refactoring_prescriptions = run_refactoring_prescription_phase(
            context,
            dag,
            findings,
            architecture_policy,
            import_diet,
            proof_xray,
        )
        packet_evidence = run_packet_evidence_phase(context)
        review_regions = run_review_regions_phase(
            context,
            dag,
            declaration_graph,
            findings,
            packet_evidence,
        )
        result = pipeline_result(
            context,
            discovery,
            dag,
            module_readiness=module_readiness,
            architecture_policy=architecture_policy,
            source_patterns=source_patterns,
            import_diet=import_diet,
            proof_xray=proof_xray,
            declaration_graph=declaration_graph,
            quality_baseline=quality_baseline,
            refactoring_prescriptions=refactoring_prescriptions,
            findings=findings,
            packet_evidence=packet_evidence,
            review_regions=review_regions,
        )
        with context.phase("rendering") as counters:
            counters["payloads"] = 1
        return result
    except ResourceLimitExceeded:
        return partial_limit_result(
            context,
            discovery=discovery,
            modules=modules,
            dag=dag,
            module_readiness=module_readiness,
            architecture_policy=architecture_policy,
            source_patterns=source_patterns,
            import_diet=import_diet,
            proof_xray=proof_xray,
            declaration_graph=declaration_graph,
            quality_baseline=quality_baseline,
            refactoring_prescriptions=refactoring_prescriptions,
            findings=findings,
            packet_evidence=packet_evidence,
            review_regions=review_regions,
        )
