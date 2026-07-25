"""Graph phases, audit enrichment, and population calibration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from ladon.audit_enrichment import apply_audit_query
from ladon.analysis.audit_surface import extract_audit_surface
from ladon.analysis.declaration_graph import summarize_declaration_graph
from ladon.analysis.findings import summarize_findings
from ladon.analysis.module_dag import summarize_module_dag
from ladon.analysis.population_calibration import (
    PopulationCandidate,
    aggregate_generated_families,
    classify_populations,
    summarize_populations,
)
from ladon.analysis.quality_baseline import summarize_quality_baseline
from ladon.analysis.refactoring_prescriptions import (
    summarize_refactoring_prescriptions,
)
from ladon.analysis.review_regions import summarize_review_regions
from ladon.analysis.witness_packet import summarize_packet_evidence
from ladon.extraction import ModuleDiscovery
from ladon.ir import LeanAuditQuery, LeanDeclaration, LeanModule
from ladon.pipeline_extraction import (
    analysis_module_roots,
    declaration_roots_for_modules,
    reference_inventory_names,
)
from ladon.pipeline_models import RunContext
from ladon.pipeline_optional import resolve_generated_family_policy


def run_module_dag_phase(
    context: RunContext,
    modules: Mapping[str, LeanModule],
    discovery: ModuleDiscovery,
) -> dict[str, Any]:
    """Summarize the module DAG for the selected analysis root."""

    with context.phase("module_dag") as counters:
        dag = summarize_module_dag(
            modules,
            chosen_roots=analysis_module_roots(context, discovery),
        )
        if context.scope_plan is not None:
            dag["analysis_scope"] = context.scope_plan.to_payload()
        dag["source_index"] = {
            "inventoryModuleCount": context.inventory_module_count,
            "indexedModuleCount": context.indexed_module_count,
            "selectedModuleCount": len(modules),
            "status": context.source_index_status,
            "cache": dict(context.source_index_cache or {}),
            "diagnostics": [
                dict(row) for row in context.source_index_diagnostics
            ],
        }
        attach_audit_surfaces(context, dag, modules)
        attach_module_populations(context, dag, modules)
        dag["scope"] = (
            context.scope_plan.scope_kind
            if context.scope_plan is not None
            else "inventory"
        )
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


def discovery_phase_reason(context: RunContext) -> str:
    """Return the recorded discovery reason for downstream partial labels."""

    timing = next(
        (
            row
            for row in reversed(context.timings)
            if row.name == "discover"
        ),
        None,
    )
    return (
        timing.reason
        if timing is not None and timing.reason
        else "source discovery retained a partial readable population"
    )


def attach_audit_surfaces(
    context: RunContext,
    dag: dict[str, Any],
    modules: Mapping[str, LeanModule],
) -> None:
    """Attach lexical audit commands and resource directives to their owners."""

    rows: list[dict[str, Any]] = []
    metadata = dag.get("module_metadata", {})
    for module in modules.values():
        path = context.repo_root / module.path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        surface = extract_audit_surface(
            module.name,
            module.path,
            text,
            declaration_count=len(module.declarations),
        )
        if not surface.commands and not surface.resource_directives:
            continue
        row = surface.to_dict()
        attach_audit_query_results(row, context.lean_audit_queries)
        rows.append(row)
        module_row = metadata.get(module.name)
        if isinstance(module_row, dict):
            module_row["commandOnly"] = surface.command_only
            module_row["auditCommandCount"] = len(surface.commands)
            module_row["resourceDirectiveCount"] = len(
                surface.resource_directives
            )
    dag["audit_surfaces"] = rows
    dag["audit_summary"] = {
        "modules": len(rows),
        "commandOnlyModules": sum(
            1 for row in rows if bool(row.get("commandOnly"))
        ),
        "auditCommands": sum(
            int(row.get("summary", {}).get("auditCommands", 0))
            for row in rows
        ),
        "resourceDirectives": sum(
            int(row.get("summary", {}).get("resourceDirectives", 0))
            for row in rows
        ),
        "backend": "text",
        "authority": "lexical_text",
    }


def attach_audit_query_results(
    surface: dict[str, Any],
    queries: Mapping[str, LeanAuditQuery],
) -> None:
    """Join helper results to stable lexical command identifiers."""

    for command in surface.get("auditCommands", []):
        if isinstance(command, dict):
            apply_audit_query(
                command,
                queries.get(str(command.get("id", ""))),
            )


def attach_module_populations(
    context: RunContext,
    dag: dict[str, Any],
    modules: Mapping[str, LeanModule],
) -> None:
    """Classify selected modules and expose authored-by-default graph rows."""

    policy, source = resolve_generated_family_policy(context)
    roots = target_source_roots(context)
    candidates = tuple(
        module_population_candidate(context.repo_root, module)
        for module in modules.values()
    )
    classifications = classify_populations(
        candidates,
        target_source_roots=roots,
        policy=policy,
    )
    by_module = {
        candidate.module: classification
        for candidate, classification in zip(candidates, classifications)
    }
    metadata = dag.get("module_metadata", {})
    for module, classification in by_module.items():
        row = metadata.get(module)
        if isinstance(row, dict):
            row["population"] = classification.population
            row["populationEvidence"] = classification.to_dict()
    attach_audit_populations(dag, by_module)
    summary = summarize_populations(
        classifications,
        selected_population="target_owned",
    )
    dag["population_calibration"] = {
        "policy": policy.to_dict() if policy is not None else None,
        "policySource": source,
        "targetSourceRoots": list(roots),
        "rows": [
            {
                "module": candidate.module,
                "path": candidate.source_path,
                **classification.to_dict(),
            }
            for candidate, classification in zip(candidates, classifications)
        ],
        "summary": summary.to_dict(),
        "generatedFamilies": [
            row.to_dict()
            for row in aggregate_generated_families(
                candidates,
                classifications,
            )
        ],
        "nonclaim": (
            "Population labels describe ownership and generation provenance, "
            "not proof correctness, theorem truth, or generator freshness."
        ),
    }
    dag["top_target_owned_fan_in"] = target_owned_fan_in_rows(
        modules,
        by_module,
    )


def attach_audit_populations(
    dag: dict[str, Any],
    classifications: Mapping[str, Any],
) -> None:
    """Thread containing-owner populations without promoting findings."""

    for surface in dag.get("audit_surfaces", []):
        if not isinstance(surface, dict):
            continue
        module = str(surface.get("module", ""))
        classification = classifications.get(module)
        population = getattr(classification, "population", "unclassified")
        surface["population"] = population
        for command in surface.get("auditCommands", []):
            if isinstance(command, dict):
                command["containingOwner"] = module
                command["containingPopulation"] = population
        for directive in surface.get("resourceDirectives", []):
            if isinstance(directive, dict):
                directive["population"] = population


def module_population_candidate(
    repo_root: Path,
    module: LeanModule,
) -> PopulationCandidate:
    """Adapt one indexed module into the calibration boundary."""

    path = repo_root / module.path
    try:
        source_size = path.stat().st_size
    except OSError:
        source_size = 0
    return PopulationCandidate(
        identifier=f"module:{module.name}",
        kind="module",
        module=module.name,
        source_path=module.path,
        source_authority="lexical_text",
        source_size_bytes=source_size,
        declaration_count=len(module.declarations),
        imports=module.imports,
    )


def target_source_roots(context: RunContext) -> tuple[str, ...]:
    """Return declared target roots from the explicit inventory boundary."""

    if context.scope_plan is None:
        return (".",)
    roots = tuple(
        str(row.get("path", "."))
        for row in context.scope_plan.inventory_boundary
    )
    return roots or (".",)


def target_owned_fan_in_rows(
    modules: Mapping[str, LeanModule],
    classifications: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return calibrated target-owned importer/target pressure."""

    target_owned = {
        module
        for module, row in classifications.items()
        if row.population == "target_owned"
    }
    rows: list[dict[str, Any]] = []
    for target in sorted(target_owned):
        all_importers = sorted(
            module.name
            for module in modules.values()
            if target in module.imports
        )
        selected = [
            importer for importer in all_importers if importer in target_owned
        ]
        rows.append(
            {
                "module": target,
                "path": modules[target].path,
                "fan_in": len(selected),
                "sample_importers": selected[:12],
                "population": (
                    "target_owned_importers_to_target_owned_targets"
                ),
                "numerator": len(selected),
                "denominator": len(all_importers),
                "exclusions": {
                    "nonTargetOwnedImporters": len(all_importers)
                    - len(selected)
                },
                "authority": "module_import_graph_and_population_policy",
            }
        )
    return sorted(
        rows,
        key=lambda row: (int(row["fan_in"]), str(row["module"])),
        reverse=True,
    )[:15]


def enrich_audit_and_declaration_populations(
    dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> None:
    """Join optional Lean declaration identity and calibrated ownership."""

    if declaration_graph is None:
        return
    declarations = [
        row
        for row in declaration_graph.get("declarations", [])
        if isinstance(row, dict)
    ]
    by_name = {
        str(row.get("declaration")): row
        for row in declarations
        if row.get("declaration")
    }
    attach_declaration_populations(dag, declaration_graph, declarations)
    for surface in dag.get("audit_surfaces", []):
        if not isinstance(surface, dict):
            continue
        for command in surface.get("auditCommands", []):
            if isinstance(command, dict):
                enrich_audit_command(command, by_name)


def enrich_audit_command(
    command: dict[str, Any],
    by_name: Mapping[str, dict[str, Any]],
) -> None:
    """Attach exact identity candidates without claiming command resolution."""

    subject = str(command.get("subject", "")).strip()
    referenced = str(
        command.get("referencedDeclaration") or subject
    ).strip()
    declaration = by_name.get(referenced)
    if declaration is None:
        if command.get("queryResult") is None:
            command["resultStatus"] = "unavailable"
            command["resultReason"] = (
                "No command-specific Lean resolution result was captured; "
                "lexical subjects are not resolved by suffix matching."
            )
        return
    command["referencedDeclaration"] = declaration.get("declaration")
    command["referencedOwner"] = declaration.get("module")
    command["referencedPopulation"] = declaration.get("population")
    command["referencedBackend"] = declaration.get("extractionBackend")
    if command.get("queryResult") is None:
        command["resultStatus"] = "unavailable"
        command["resultReason"] = (
            "An exact extracted declaration identity exists, but no "
            "command-specific Lean resolution or query result was captured."
        )


def attach_declaration_populations(
    dag: dict[str, Any],
    declaration_graph: dict[str, Any],
    declarations: list[dict[str, Any]],
) -> None:
    """Classify declaration rows from module and Lean generation evidence."""

    module_rows = dag.get("population_calibration", {}).get("rows", [])
    module_populations = {
        str(row.get("module")): str(row.get("population", "unclassified"))
        for row in module_rows
        if isinstance(row, dict)
    }
    counts: dict[str, int] = {}
    by_declaration: dict[str, str] = {}
    for row in declarations:
        population, authority = declaration_population(
            row,
            module_populations,
        )
        row["population"] = population
        row["populationAuthority"] = authority
        counts[population] = counts.get(population, 0) + 1
        by_declaration[str(row.get("declaration", ""))] = population
    declaration_graph["population_calibration"] = {
        "selectedPopulation": "target_owned",
        "rawCount": len(declarations),
        "counts": dict(sorted(counts.items())),
        "exclusions": {
            population: count
            for population, count in sorted(counts.items())
            if population != "target_owned"
        },
        "nonclaim": (
            "Declaration populations preserve extraction authority and do not "
            "state proof correctness or theorem truth."
        ),
    }
    edges = declaration_graph.get("edges", {})
    declaration_graph["top_target_owned_fan_in"] = (
        calibrated_declaration_ranking(edges, by_declaration, "fan_in")
    )
    declaration_graph["top_target_owned_fan_out"] = (
        calibrated_declaration_ranking(edges, by_declaration, "fan_out")
    )


def calibrated_declaration_ranking(
    raw_edges: Any,
    populations: Mapping[str, str],
    metric: str,
) -> list[dict[str, Any]]:
    """Rank an independently recomputed target-owned declaration subgraph."""

    edges = normalized_declaration_edges(raw_edges)
    if metric == "fan_in":
        relationships = reverse_declaration_relationships(edges)
    elif metric == "fan_out":
        relationships = edges
    else:
        raise ValueError(f"unsupported declaration metric: {metric}")
    rows = [
        calibrated_declaration_row(
            declaration,
            targets,
            populations,
            metric,
        )
        for declaration, targets in relationships.items()
        if populations.get(declaration) == "target_owned"
    ]
    return sorted(
        rows,
        key=lambda row: (
            -int(row[metric]),
            str(row["declaration"]),
        ),
    )[:15]


def normalized_declaration_edges(raw: Any) -> dict[str, tuple[str, ...]]:
    """Return only string-to-string declaration relationships."""

    if not isinstance(raw, Mapping):
        return {}
    return {
        str(source): tuple(
            sorted(
                str(target)
                for target in targets
                if isinstance(target, str)
            )
        )
        for source, targets in raw.items()
        if isinstance(source, str) and isinstance(targets, Sequence)
    }


def reverse_declaration_relationships(
    edges: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    """Reverse declaration relationships while retaining zero-degree rows."""

    reverse: dict[str, list[str]] = {
        declaration: [] for declaration in edges
    }
    for source, targets in edges.items():
        for target in targets:
            reverse.setdefault(target, []).append(source)
    return {
        declaration: tuple(sorted(sources))
        for declaration, sources in reverse.items()
    }


def calibrated_declaration_row(
    declaration: str,
    relationships: Sequence[str],
    populations: Mapping[str, str],
    metric: str,
) -> dict[str, Any]:
    """Expose selected and raw populations without carrying raw inflation."""

    selected = [
        target
        for target in relationships
        if populations.get(target) == "target_owned"
    ]
    denominator = len(relationships)
    return {
        "declaration": declaration,
        metric: len(selected),
        "rawMetric": denominator,
        "population": "target_owned_to_target_owned",
        "numerator": len(selected),
        "denominator": denominator,
        "exclusions": {
            "nonTargetOwnedEndpoints": denominator - len(selected)
        },
        "authority": "parser_candidate_graph_and_population_policy",
    }


def declaration_population(
    row: Mapping[str, Any],
    module_populations: Mapping[str, str],
) -> tuple[str, str]:
    """Apply imported/compiler evidence before containing-module ownership."""

    if bool(row.get("importedStub")):
        return "imported", "lean_imported_stub"
    if bool(row.get("compilerGenerated")):
        authority = str(row.get("compilerAuthority") or "unclassified")
        if authority == "lean_environment" and row.get("compilerToolchain"):
            return "compiler_generated", authority
        return "unclassified", "incomplete_compiler_generation_evidence"
    module = str(row.get("module", ""))
    population = module_populations.get(module, "unclassified")
    return population, "containing_module_population"


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
            counters["declarations"] = int(
                declaration_graph["declaration_count"]
            )
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
        counters["prescriptions"] = len(
            refactoring_prescriptions["rows"]
        )
        return refactoring_prescriptions


def run_packet_evidence_phase(
    context: RunContext,
) -> list[dict[str, Any]]:
    """Summarize optional OpenSpec/proof packet evidence directories."""

    if context.packet_dirs:
        with context.phase("packet_evidence") as counters:
            packet_evidence = [
                summarize_packet_evidence(
                    packet_dir,
                    profile=context.packet_profile,
                )
                for packet_dir in context.packet_dirs
            ]
            counters["packet_dirs"] = len(packet_evidence)
            return packet_evidence
    context.record_skipped(
        "packet_evidence",
        "no packet directories requested",
    )
    return []


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
