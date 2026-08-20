"""Partial-result construction for interrupted pipeline runs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.extraction import ModuleDiscovery
from ladon.ir import LeanModule
from ladon.pipeline_calibration import run_module_dag_phase
from ladon.pipeline_extraction import (
    add_index_counters,
    finalize_discovery_phase,
    indexed_discovery,
)
from ladon.pipeline_models import (
    REQUIRED_PHASES,
    PipelineResult,
    RunContext,
    pipeline_result,
)
from ladon.progress import ResourceLimitExceeded


def partial_limit_result(
    context: RunContext,
    *,
    discovery: ModuleDiscovery | None,
    modules: Mapping[str, LeanModule],
    dag: dict[str, Any] | None,
    **values: Any,
) -> PipelineResult:
    """Preserve completed evidence and suppress unfinished derived metrics."""

    retained = retained_limit_discovery(context, discovery)
    retained_modules = retained_limit_modules(context, modules, retained)
    reason = resource_limit_reason(context)
    record_limit_skips(context, reason)
    partial_dag = dag or incomplete_module_dag(
        retained_modules,
        context=context,
        reason=reason,
    )
    partial_dag["completeness"] = {
        "status": "partial",
        "reason": reason,
        "metricsSuppressed": dag is None,
    }
    return pipeline_result(
        context,
        retained,
        partial_dag,
        **values,
    )


def retained_limit_discovery(
    context: RunContext,
    discovery: ModuleDiscovery | None,
) -> ModuleDiscovery:
    """Return validated discovery or re-raise the controlling early limit."""

    retained = discovery or context.retained_discovery
    if retained is not None:
        return retained
    failure = context.limit_failure or {}
    raise ResourceLimitExceeded(
        kind=str(failure.get("kind", "resource")),
        phase=str(failure.get("phase", "discover")),
        observed=failure.get("observed", 0),
        limit=failure.get("limit", 0),
    )


def retained_limit_modules(
    context: RunContext,
    modules: Mapping[str, LeanModule],
    discovery: ModuleDiscovery,
) -> dict[str, LeanModule]:
    """Select the most authoritative completed module inventory."""

    if modules:
        return dict(modules)
    if context.retained_modules:
        return dict(context.retained_modules)
    return dict(discovery.modules)


def resource_limit_reason(context: RunContext) -> str:
    """Return one stable human-readable cause for a partial resource run."""

    failure = context.limit_failure or {}
    return str(
        failure.get(
            "reason",
            "configured resource limit stopped analysis",
        )
    )


def record_limit_skips(context: RunContext, reason: str) -> None:
    """Mark every phase not started after a controlling limit crossing."""

    recorded = {timing.name for timing in context.timings}
    for name in REQUIRED_PHASES:
        if name not in recorded:
            context.record_skipped(
                name,
                f"not run after resource limit: {reason}",
            )


def incomplete_module_dag(
    modules: Mapping[str, LeanModule],
    *,
    context: RunContext,
    reason: str,
) -> dict[str, Any]:
    """Return schema-valid inventory facts without claiming completed metrics."""

    return {
        "scope": (
            context.scope_plan.scope_kind
            if context.scope_plan is not None
            else "unknown"
        ),
        "method": "partial_source_inventory",
        "module_count": len(modules),
        "edge_count": sum(
            len(module.imports) for module in modules.values()
        ),
        "acyclic": None,
        "topological_layer_count": 0,
        "facade_module_count": 0,
        "generated_module_count": 0,
        "duplicate_import_count": 0,
        "module_metadata": {
            name: {
                "path": module.path,
                "lineCount": module.line_count,
                "declarationCount": len(module.declarations),
            }
            for name, module in sorted(modules.items())
        },
        "analysis_scope": (
            context.scope_plan.to_payload()
            if context.scope_plan is not None
            else None
        ),
        "source_index": {
            "inventoryModuleCount": context.inventory_module_count,
            "selectedModuleCount": len(modules),
            "cache": dict(context.source_index_cache or {}),
        },
        "suppressedMetrics": [
            {
                "section": "module_dag",
                "reason": reason,
            }
        ],
    }


def discovery_partial_result(
    context: RunContext,
    *,
    blocked_phase: str,
    reason: str,
) -> PipelineResult:
    """Build trustworthy text discovery evidence after a prerequisite failure."""

    with context.phase("discover") as counters:
        resolved = indexed_discovery(context)
        discovery = resolved.discovery
        counters["modules"] = len(discovery.modules)
        add_index_counters(counters, resolved)
    finalize_discovery_phase(context, resolved)
    context.record_skipped(blocked_phase, reason)
    context.record_skipped(
        "indexing",
        f"{blocked_phase} did not produce backend IR",
    )
    dag = run_module_dag_phase(context, discovery.modules, discovery)
    return PipelineResult(
        context=context,
        discovery=discovery,
        module_dag=dag,
    )
