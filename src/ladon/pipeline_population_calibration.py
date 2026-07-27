"""Module population calibration and target-owned graph projections."""

from __future__ import annotations

from typing import Any, Mapping

from ladon.analysis.population_calibration import (
    PopulationCandidate,
    aggregate_generated_families,
    classify_populations,
    summarize_populations,
)
from ladon.ir import LeanModule
from ladon.pipeline_models import RunContext
from ladon.pipeline_optional import resolve_generated_family_policy
from ladon.source_index_models import SourceIndex


def attach_module_populations(
    context: RunContext,
    dag: dict[str, Any],
    modules: Mapping[str, LeanModule],
) -> None:
    """Classify selected modules and expose target-owned graph rows."""

    policy, source = resolve_generated_family_policy(context)
    roots = target_source_roots(context)
    source_sizes = (
        {
            entry.name: entry.source_bytes
            for entry in context.source_index.entries
        }
        if context.source_index is not None
        else {}
    )
    candidates = tuple(
        module_population_candidate(
            context.source_index,
            module,
            source_size_bytes=source_sizes.get(module.name),
        )
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
    _attach_metadata_populations(dag, by_module)
    attach_audit_populations(dag, by_module)
    dag["population_calibration"] = _population_calibration_payload(
        candidates,
        classifications,
        roots=roots,
        policy=policy,
        policy_source=source,
    )
    dag["top_target_owned_fan_in"] = target_owned_fan_in_rows(
        modules,
        by_module,
    )
    dag["top_target_owned_fan_out"] = target_owned_fan_out_rows(
        modules,
        by_module,
    )
    dag["top_target_owned_large_modules"] = target_owned_large_module_rows(
        modules,
        by_module,
    )
    dag["legacy_population_compatibility"] = (
        _legacy_population_compatibility()
    )


def _attach_metadata_populations(
    dag: dict[str, Any],
    classifications: Mapping[str, Any],
) -> None:
    metadata = dag.get("module_metadata", {})
    for module, classification in classifications.items():
        row = metadata.get(module)
        if isinstance(row, dict):
            row["population"] = classification.population
            row["populationEvidence"] = classification.to_dict()


def _population_calibration_payload(
    candidates: tuple[PopulationCandidate, ...],
    classifications: tuple[Any, ...],
    *,
    roots: tuple[str, ...],
    policy: Any,
    policy_source: str,
) -> dict[str, Any]:
    summary = summarize_populations(
        classifications,
        selected_population="target_owned",
    )
    return {
        "policy": policy.to_dict() if policy is not None else None,
        "policySource": policy_source,
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


def _legacy_population_compatibility() -> dict[str, Any]:
    return {
        "top_handwritten_fan_in": legacy_population_field(
            "non_generated_tag_importers_to_non_generated_tag_targets",
            "top_target_owned_fan_in",
        ),
        "top_handwritten_fan_out": legacy_population_field(
            "non_generated_tag_modules_to_selected_internal_targets",
            "top_target_owned_fan_out",
        ),
        "top_large_handwritten_modules": legacy_population_field(
            "modules_without_lexical_generated_tag",
            "top_target_owned_large_modules",
        ),
    }


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
        _attach_surface_population(surface, module, population)


def _attach_surface_population(
    surface: dict[str, Any],
    module: str,
    population: str,
) -> None:
    for command in surface.get("auditCommands", []):
        if isinstance(command, dict):
            command["containingOwner"] = module
            command["containingPopulation"] = population
    for directive in surface.get("resourceDirectives", []):
        if isinstance(directive, dict):
            directive["population"] = population


def module_population_candidate(
    source_index: SourceIndex | None,
    module: LeanModule,
    *,
    source_size_bytes: int | None = None,
) -> PopulationCandidate:
    """Adapt one indexed module into the calibration boundary."""

    source_size = source_size_bytes
    if source_size is None:
        source_size = (
            next(
                (
                    entry.source_bytes
                    for entry in source_index.entries
                    if entry.name == module.name
                ),
                0,
            )
            if source_index is not None
            else 0
        )
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

    target_owned = _target_owned_modules(classifications)
    importers: dict[str, list[str]] = {}
    for module in modules.values():
        for target in set(module.imports):
            if target in target_owned:
                importers.setdefault(target, []).append(module.name)
    rows = [
        _target_owned_fan_in_row(
            target,
            modules,
            target_owned,
            importers=importers.get(target, []),
        )
        for target in sorted(target_owned)
    ]
    return sorted(
        rows,
        key=lambda row: (int(row["fan_in"]), str(row["module"])),
        reverse=True,
    )[:15]


def _target_owned_fan_in_row(
    target: str,
    modules: Mapping[str, LeanModule],
    target_owned: set[str],
    *,
    importers: list[str] | None = None,
) -> dict[str, Any]:
    all_importers = (
        sorted(importers)
        if importers is not None
        else sorted(
            module.name
            for module in modules.values()
            if target in module.imports
        )
    )
    selected = [
        importer for importer in all_importers if importer in target_owned
    ]
    return {
        "module": target,
        "path": modules[target].path,
        "fan_in": len(selected),
        "sample_importers": selected[:12],
        "population": "target_owned_importers_to_target_owned_targets",
        "numerator": len(selected),
        "denominator": len(all_importers),
        "exclusions": {
            "nonTargetOwnedImporters": len(all_importers) - len(selected)
        },
        "authority": "module_import_graph_and_population_policy",
    }


def target_owned_fan_out_rows(
    modules: Mapping[str, LeanModule],
    classifications: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Rank imports inside the exact calibrated target-owned population."""

    target_owned = _target_owned_modules(classifications)
    rows = [
        _target_owned_fan_out_row(module, modules, target_owned)
        for module in sorted(target_owned)
    ]
    return sorted(
        rows,
        key=lambda row: (-int(row["fan_out"]), str(row["module"])),
    )[:15]


def _target_owned_fan_out_row(
    module: str,
    modules: Mapping[str, LeanModule],
    target_owned: set[str],
) -> dict[str, Any]:
    internal = sorted(
        target for target in set(modules[module].imports) if target in modules
    )
    selected = [target for target in internal if target in target_owned]
    return {
        "module": module,
        "path": modules[module].path,
        "fan_out": len(selected),
        "rawMetric": len(internal),
        "sample_imports": selected[:12],
        "roles": [],
        "population": "target_owned_importers_to_target_owned_targets",
        "numerator": len(selected),
        "denominator": len(internal),
        "exclusions": {
            "nonTargetOwnedTargets": len(internal) - len(selected)
        },
        "authority": "module_import_graph_and_population_policy",
    }


def target_owned_large_module_rows(
    modules: Mapping[str, LeanModule],
    classifications: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return largest modules in the exact target-owned population."""

    rows = [
        {
            "module": module,
            "path": modules[module].path,
            "lineCount": int(modules[module].line_count),
            "population": "target_owned",
            "authority": "source_index_and_population_policy",
        }
        for module, classification in classifications.items()
        if classification.population == "target_owned"
        and modules[module].line_count > 0
    ]
    return sorted(
        rows,
        key=lambda row: (-int(row["lineCount"]), str(row["module"])),
    )[:15]


def legacy_population_field(
    effective_population: str,
    migration_target: str,
) -> dict[str, Any]:
    """Disclose the bounded compatibility meaning of a legacy field."""

    return {
        "status": "deprecated_compatibility",
        "effectivePopulation": effective_population,
        "migrationTarget": migration_target,
        "authority": "lexical_generated_tag_filter",
        "nonclaim": (
            "The legacy field name is not authorship evidence and does not "
            "mean that target-owned source was written by a human."
        ),
    }


def _target_owned_modules(
    classifications: Mapping[str, Any],
) -> set[str]:
    return {
        module
        for module, row in classifications.items()
        if row.population == "target_owned"
    }


__all__ = [
    "attach_audit_populations",
    "attach_module_populations",
    "legacy_population_field",
    "module_population_candidate",
    "target_owned_fan_in_rows",
    "target_owned_fan_out_rows",
    "target_owned_large_module_rows",
    "target_source_roots",
]
