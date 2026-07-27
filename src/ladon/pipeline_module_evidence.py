"""Module-DAG selection, scope identities, and boundary evidence."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ladon.analysis.module_dag import summarize_module_dag
from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.extraction import ModuleDiscovery
from ladon.ir import LeanModule
from ladon.pipeline_extraction import analysis_module_roots
from ladon.pipeline_models import RunContext
from ladon.scope import ScopePlan
from ladon.source_index_models import (
    SOURCE_INDEX_IMPORTS_COVERAGE,
    SourceIndex,
)


def selected_module_dag(
    context: RunContext,
    modules: Mapping[str, LeanModule],
    discovery: ModuleDiscovery,
) -> dict[str, Any]:
    """Run pure DAG analysis with scope and source identities resolved once."""

    plan = context.scope_plan
    source_index = context.source_index
    root_view = root_view_configuration(context)
    return summarize_module_dag(
        modules,
        chosen_roots=analysis_module_roots(context, discovery),
        full_inventory_modules=(
            source_index.discovered_module_paths if source_index is not None else None
        ),
        full_inventory_fingerprint=(
            source_index.fingerprint if source_index is not None else None
        ),
        scope_source_fingerprint=scope_source_fingerprint(
            plan,
            source_index,
        ),
        scope_fingerprint=plan.fingerprint if plan is not None else None,
        selected_import_coverage=selected_import_coverage(context, modules),
        root_view_auxiliary=root_view["auxiliary"],
        root_view_population=root_view["population"],
        root_view_reason=root_view["reason"],
    )


def scope_source_fingerprint(
    plan: ScopePlan | None,
    source_index: SourceIndex | None,
) -> str | None:
    """Return the plan/index join identity without nested fallback logic."""

    if plan is not None:
        return str(plan.source_index_fingerprint)
    return source_index.fingerprint if source_index is not None else None


def source_index_summary(
    context: RunContext,
    selected_module_count: int,
) -> dict[str, Any]:
    """Return the report-facing source-index population envelope."""

    return {
        "inventoryModuleCount": context.inventory_module_count,
        "indexedModuleCount": context.indexed_module_count,
        "selectedModuleCount": selected_module_count,
        "status": context.source_index_status,
        "cache": dict(context.source_index_cache or {}),
        "diagnostics": [dict(row) for row in context.source_index_diagnostics],
    }


def attach_boundary_membership_evidence(
    dag: dict[str, Any],
    source_index: SourceIndex | None,
) -> None:
    """Attach exact fingerprint-bound inventory lookup results to boundaries."""

    boundaries = dag.get("import_boundaries")
    index_summary = dag.get("source_index")
    if not isinstance(boundaries, list) or not isinstance(index_summary, dict):
        return
    inventory_paths = (
        source_index.discovered_module_paths if source_index is not None else {}
    )
    indexed_paths = source_index.paths if source_index is not None else {}
    fingerprint = source_index.fingerprint if source_index is not None else None
    membership = boundary_membership_rows(
        boundary_targets(boundaries),
        inventory_paths,
        indexed_paths,
        fingerprint,
    )
    index_summary["boundaryMembershipEvidence"] = membership
    target_indexes = {row["module"]: index for index, row in enumerate(membership)}
    rewrite_boundary_membership_refs(
        boundaries,
        target_indexes,
        inventory_paths,
        indexed_paths,
    )


def boundary_targets(boundaries: list[Any]) -> list[str]:
    """Return stable non-empty boundary target identities."""

    return sorted(
        {
            str(row.get("targetModule"))
            for row in boundaries
            if isinstance(row, dict) and row.get("targetModule")
        }
    )


def boundary_membership_rows(
    targets: Sequence[str],
    inventory_paths: Mapping[str, str],
    indexed_paths: Mapping[str, str],
    fingerprint: str | None,
) -> list[dict[str, Any]]:
    """Record exact source-index membership lookup results."""

    return [
        {
            "module": target,
            "present": target in inventory_paths,
            "path": inventory_paths.get(target),
            "indexEntryStatus": _index_entry_status(
                target,
                inventory_paths,
                indexed_paths,
            ),
            "sourceIndexFingerprint": fingerprint,
            "authority": "source_index_manifest",
        }
        for target in targets
    ]


def rewrite_boundary_membership_refs(
    boundaries: list[Any],
    target_indexes: Mapping[str, int],
    inventory_paths: Mapping[str, str],
    indexed_paths: Mapping[str, str],
) -> None:
    """Point boundary rows at their exact membership result."""

    for row in boundaries:
        if not isinstance(row, dict):
            continue
        target = str(row.get("targetModule", ""))
        evidence = row.get("evidenceRefs")
        if not isinstance(evidence, list) or target not in target_indexes:
            continue
        rewrite_inventory_reference(
            evidence,
            index=target_indexes[target],
            present=target in inventory_paths,
            index_entry_status=_index_entry_status(
                target,
                inventory_paths,
                indexed_paths,
            ),
        )


def rewrite_inventory_reference(
    evidence: list[Any],
    *,
    index: int,
    present: bool,
    index_entry_status: str,
) -> None:
    """Rewrite one row's canonical inventory reference in place."""

    for reference in evidence:
        if (
            isinstance(reference, dict)
            and reference.get("type") == "source_index_inventory"
        ):
            reference["pointer"] = (
                f"#/sections/module_dag/source_index/boundaryMembershipEvidence/{index}"
            )
            reference["present"] = present
            reference["indexEntryStatus"] = index_entry_status


def _index_entry_status(
    target: str,
    inventory_paths: Mapping[str, str],
    indexed_paths: Mapping[str, str],
) -> str:
    """Distinguish manifest membership from lexical-entry availability."""

    if target in indexed_paths:
        return "available"
    if target in inventory_paths:
        return "unavailable"
    return "absent"


def root_view_configuration(context: RunContext) -> dict[str, Any]:
    """Describe whether chosen roots are primary or auxiliary navigation."""

    plan = context.scope_plan
    if plan is None:
        return {
            "auxiliary": False,
            "population": "legacy_discovery_population",
            "reason": None,
        }
    if plan.scope_kind != "inventory":
        return {
            "auxiliary": False,
            "population": "selected_scope_module_population",
            "reason": None,
        }
    if plan.resolved_navigation_roots:
        return {
            "auxiliary": True,
            "population": "inventory_auxiliary_navigation_view",
            "reason": (
                "explicit navigation roots do not narrow the inventory population"
            ),
        }
    return {
        "auxiliary": False,
        "population": "inventory_module_population",
        "reason": (
            "requested navigation roots did not resolve"
            if plan.requested_navigation_roots
            else "inventory scope has no explicit navigation root"
        ),
    }


def discovery_phase_reason(context: RunContext) -> str:
    """Return the recorded discovery reason for downstream partial labels."""

    timing = next(
        (row for row in reversed(context.timings) if row.name == "discover"),
        None,
    )
    return (
        timing.reason
        if timing is not None and timing.reason
        else "source discovery retained a partial readable population"
    )


def selected_import_coverage(
    context: RunContext,
    modules: Mapping[str, LeanModule],
) -> CollectionCoverage:
    """Return truthful selected-import observation for boundary derivation."""

    visible = sum(
        len(module.import_sites or module.imports) for module in modules.values()
    )
    plan = context.scope_plan
    source_fingerprint = (
        context.source_index.fingerprint if context.source_index is not None else None
    )
    common: dict[str, Any] = {
        "identity": "module_dag.import_boundaries",
        "pointer": "#/sections/module_dag/import_boundaries",
        "visible": visible,
        "population": "selected_lexical_import_occurrences",
        "scope": plan.scope_kind if plan is not None else context.analysis_scope,
        "authority": "lexical_text_and_source_index_membership",
        "source_fingerprint": source_fingerprint,
        "scope_fingerprint": plan.fingerprint if plan is not None else None,
    }
    if context.source_index is not None and context.source_index_status == "complete":
        return CollectionCoverage.exact(total=visible, **common)
    return CollectionCoverage.unknown(
        observed_lower_bound=visible,
        completeness="partial",
        causes=_selected_import_coverage_causes(context),
        **common,
    )


def _selected_import_coverage_causes(
    context: RunContext,
) -> tuple[CoverageCause, ...]:
    if context.source_index is not None:
        upstream = context.source_index.coverage_registry().collections.get(
            SOURCE_INDEX_IMPORTS_COVERAGE
        )
        if upstream is not None and upstream.causes:
            return upstream.causes
    return (
        CoverageCause(
            kind="analysis",
            identifier="coverage.source_index_unavailable",
            detail=(
                "selected import coverage lacks a complete source-index population"
            ),
        ),
    )


__all__ = [
    "attach_boundary_membership_evidence",
    "boundary_membership_rows",
    "boundary_targets",
    "discovery_phase_reason",
    "rewrite_boundary_membership_refs",
    "rewrite_inventory_reference",
    "root_view_configuration",
    "scope_source_fingerprint",
    "selected_import_coverage",
    "selected_module_dag",
    "source_index_summary",
]
