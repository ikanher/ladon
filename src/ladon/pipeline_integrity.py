"""Pipeline wiring for declaration and generated-family integrity surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.analysis.declaration_integrity import analyze_declaration_integrity
from ladon.analysis.generated_family_candidate_adapters import (
    analyze_generated_family_candidate_surface,
)
from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    CandidateProfile,
)
from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.extraction import ModuleDiscovery
from ladon.pipeline_extraction import analysis_module_roots
from ladon.pipeline_models import RunContext

DECLARATION_COVERAGE_FIELDS = (
    "declaration_collision_coverage",
    "declaration_block_duplicate_coverage",
    "declaration_file_duplicate_coverage",
    "declaration_source_shape_coverage",
    "declaration_coreachable_coverage",
)


def attach_integrity_surfaces(
    context: RunContext,
    dag: dict[str, Any],
    discovery: ModuleDiscovery,
) -> None:
    """Attach both post-population integrity analyses without source rescans."""

    source_index = context.source_index
    if source_index is None:
        return
    declaration = analyze_declaration_integrity(
        source_index.modules,
        content_hashes={
            entry.name: entry.content_sha256 for entry in source_index.entries
        },
        source_fingerprint=source_index.fingerprint,
        scope_fingerprint=_scope_fingerprint(context),
        inventory_complete=source_index.index_status == "complete",
        selected_edges=_selected_edges(dag),
        selected_roots=analysis_module_roots(context, discovery),
        selected_graph_coverage=_selected_graph_coverage(context, dag),
    )
    dag["declaration_integrity"] = declaration.to_dict()
    for field, coverage in zip(
        DECLARATION_COVERAGE_FIELDS,
        declaration.coverage_rows,
    ):
        dag[field] = coverage.to_dict()
    profile = context.generated_family_candidate_profile or BUILTIN_CANDIDATE_PROFILE
    generated = analyze_generated_family_candidate_surface(
        dag,
        source_index,
        profile=_candidate_profile(profile),
    )
    dag.update(generated.to_module_dag_fields())


def _selected_edges(dag: Mapping[str, Any]) -> Mapping[str, tuple[str, ...]]:
    """Return deterministic selected graph edges or an empty graph."""

    raw = dag.get("edges")
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(source): tuple(sorted(str(target) for target in targets))
        for source, targets in raw.items()
        if isinstance(targets, list)
    }


def _selected_graph_coverage(
    context: RunContext,
    dag: Mapping[str, Any],
) -> CollectionCoverage:
    """Describe whether every selected graph node is available exactly."""

    edges = _selected_edges(dag)
    metadata = dag.get("module_metadata")
    visible = len(edges)
    common = {
        "identity": "module_dag.selected_graph_nodes",
        "pointer": "#/sections/module_dag/module_metadata",
        "visible": visible,
        "population": "selected_module_graph_nodes",
        "scope": (
            context.scope_plan.scope_kind
            if context.scope_plan is not None
            else context.analysis_scope
        ),
        "authority": "module_import_graph",
        "source_fingerprint": (
            context.source_index.fingerprint
            if context.source_index is not None
            else None
        ),
        "scope_fingerprint": _scope_fingerprint(context),
    }
    if (
        context.source_index_status == "complete"
        and isinstance(metadata, Mapping)
        and set(edges) == {str(name) for name in metadata}
    ):
        return CollectionCoverage.exact(total=visible, **common)
    return CollectionCoverage.unknown(
        observed_lower_bound=visible,
        completeness="partial",
        causes=(
            CoverageCause(
                kind="analysis",
                identifier="declaration_integrity.selected_graph_incomplete",
                detail=(
                    "selected module graph does not have exact complete node coverage"
                ),
            ),
        ),
        **common,
    )


def _scope_fingerprint(context: RunContext) -> str | None:
    """Return the selected scope identity used by both integrity passes."""

    return context.scope_plan.fingerprint if context.scope_plan is not None else None


def _candidate_profile(value: object) -> CandidateProfile:
    """Narrow the run-context profile without accepting lookalike mappings."""

    if not isinstance(value, CandidateProfile):
        raise TypeError("generated-family candidate profile must be a CandidateProfile")
    return value
