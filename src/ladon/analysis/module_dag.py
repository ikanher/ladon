"""Pure module-import DAG analysis for Ladon's clean core.

Edges point from an importing module to the modules it imports. That direction
matches the way a reviewer reads dependency pull: root modules reach their
implementation dependencies by following outgoing edges.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from ladon.analysis.import_boundaries import (
    classify_import_boundaries,
    import_is_inside_scope,
    owned_top_namespaces,
    same_top_namespace as same_top_namespace,  # noqa: F401
)
from ladon.analysis.module_dag_inventory import (
    ModuleInventoryIndex as _ModuleInventoryIndex,
    build_module_inventory_index as _module_inventory_index,
    classify_facade_subtype as _facade_subtype,
    facade_names as _facade_modules,
    facade_subtype_counts as _facade_subtype_summary,
    matching_module_names as _modules_matching_filters,
    top_facade_rows as _top_facade_like_modules,
    top_fan_in_rows as _top_fan_in,
    top_fan_out_rows as _top_fan_out,
)
from ladon.analysis.module_naming import (
    generated_family_summary,
    generator_family,
    module_name_smell_rows,
    module_name_smell_summary,
)
from ladon.analysis.root_applicability import root_applicability
from ladon.coverage import CollectionCoverage
from ladon.ir import LeanModule


MAX_LARGE_MODULE_ROWS = 20
MAX_SOURCE_SMELL_ROWS = 50
MAX_TEXT_DECLARATION_ROWS = 10_000


def summarize_module_dag(
    modules: Mapping[str, LeanModule],
    *,
    chosen_roots: Sequence[str] = (),
    full_inventory_modules: Iterable[str] | None = None,
    full_inventory_fingerprint: str | None = None,
    scope_source_fingerprint: str | None = None,
    scope_fingerprint: str | None = None,
    selected_import_coverage: CollectionCoverage | None = None,
    root_view_auxiliary: bool = False,
    root_view_population: str = "selected_module_import_graph",
    root_view_reason: str | None = None,
) -> dict[str, Any]:
    """Summarize a Lean module import graph without filesystem side effects."""

    module_names = sorted(modules)
    edges = module_edges(modules)
    reverse_edges = reverse_module_edges(module_names, edges)
    components = tarjan_scc(module_names, edges)
    cyclic_components = cyclic_module_components(components, edges)
    acyclic = not cyclic_components
    ranks = module_ranks(module_names, edges) if acyclic else {}
    layer_widths = summarize_layers(ranks)
    selected_roots = known_roots(chosen_roots, modules)
    reachability = reachability_summary(modules, edges, selected_roots)
    reachability_applicability = root_applicability(
        selected_roots,
        population=root_view_population,
        auxiliary=root_view_auxiliary,
        reason=root_view_reason,
    )
    duplicate_rows = duplicate_imports(modules)
    lexical_rows = lexical_marker_rows(modules)
    boundaries = classify_import_boundaries(
        modules,
        chosen_roots=chosen_roots,
        full_inventory_modules=full_inventory_modules,
        full_inventory_fingerprint=full_inventory_fingerprint,
        scope_source_fingerprint=scope_source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        selected_import_coverage=selected_import_coverage,
    )
    missing_import_rows = (
        boundaries.missing_internal_imports()
        if full_inventory_modules is not None
        else missing_internal_imports(modules, chosen_roots)
    )
    naming_rows = module_name_smell_rows(modules)

    inventory = _module_inventory_index(modules)
    metadata = _module_metadata(modules, inventory)
    root_modules = root_like_modules(reverse_edges)
    facades = _facade_modules(inventory)
    return {
        "scope": "repo_inventory",
        "method": "repo_wide_module_import_dag",
        "module_count": len(module_names),
        "edge_count": sum(len(targets) for targets in edges.values()),
        "acyclic": acyclic,
        "scc_count": len(components),
        **cycle_summary(cyclic_components),
        "max_rank": max(ranks.values(), default=0),
        "topological_layer_count": len(layer_widths),
        "layer_widths": layer_widths[:80],
        "widest_layers": widest_layers(layer_widths),
        "top_fan_in": _top_fan_in(
            modules,
            reverse_edges,
            inventory,
            population="all_importers_to_all_targets",
        ),
        "top_fan_out": _top_fan_out(modules, edges, inventory),
        "top_handwritten_fan_in": _top_fan_in(
            modules,
            reverse_edges,
            inventory,
            excluded_tags=("generated",),
            excluded_importer_tags=("generated",),
            population="handwritten_importers_to_handwritten_targets",
        ),
        "top_generated_importer_fan_in": _top_fan_in(
            modules,
            reverse_edges,
            inventory,
            included_importer_tags=("generated",),
            population="generated_importers_to_all_targets",
        ),
        "top_generated_target_fan_in": _top_fan_in(
            modules,
            reverse_edges,
            inventory,
            included_tags=("generated",),
            population="all_importers_to_generated_targets",
        ),
        "top_handwritten_fan_out": _top_fan_out(
            modules,
            edges,
            inventory,
            excluded_tags=("generated",),
        ),
        "top_facade_fan_out": _top_fan_out(
            modules,
            edges,
            inventory,
            included_roles=("facade",),
        ),
        "top_implementation_fan_out": _top_fan_out(
            modules,
            edges,
            inventory,
            excluded_tags=("generated",),
            excluded_roles=("facade",),
        ),
        "root_like_modules": root_modules[:20],
        "root_like_module_count": len(root_modules),
        "facade_modules": facades[:20],
        "facade_module_count": len(facades),
        "facade_subtype_summary": _facade_subtype_summary(inventory),
        "top_facade_like_modules": _top_facade_like_modules(modules, inventory),
        "root_direct_import_closures": root_direct_import_closures(
            edges, selected_roots
        ),
        "root_reachability": reachability_applicability,
        **reachability,
        "module_metadata": metadata,
        "text_declaration_summary": text_declaration_summary(metadata),
        "generated_module_count": module_count_with_tag(modules, "generated"),
        "generated_family_summary": generated_family_summary(modules),
        "module_name_smells": naming_rows[:MAX_SOURCE_SMELL_ROWS],
        "module_name_smell_count": len(naming_rows),
        "module_name_smell_summary": module_name_smell_summary(naming_rows),
        "top_large_modules": top_large_modules(modules),
        "top_large_handwritten_modules": top_large_modules(
            modules, excluded_tags=("generated",)
        ),
        "duplicate_imports": duplicate_rows,
        "duplicate_import_count": len(duplicate_rows),
        "duplicate_import_family_summary": duplicate_import_family_summary(
            duplicate_rows
        ),
        "missing_internal_imports": missing_import_rows[:MAX_SOURCE_SMELL_ROWS],
        "missing_internal_import_count": len(missing_import_rows),
        "import_boundaries": boundaries.row_dicts(),
        "import_boundary_count": len(boundaries.rows),
        "import_boundary_summary": boundaries.counts(),
        "import_boundary_coverage": boundaries.coverage.to_dict(),
        "lexical_markers": lexical_rows[:MAX_SOURCE_SMELL_ROWS],
        "lexical_marker_summary": lexical_marker_summary(lexical_rows),
        "import_sites": import_sites(modules, edges),
        "edges": edges,
    }


def module_edges(modules: Mapping[str, LeanModule]) -> dict[str, list[str]]:
    """Return importer -> imported-module edges restricted to known modules."""

    return {
        name: sorted({imported for imported in module.imports if imported in modules})
        for name, module in modules.items()
    }


def module_metadata(modules: Mapping[str, LeanModule]) -> dict[str, dict[str, Any]]:
    """Return source-level module metadata for report filtering and triage."""

    return _module_metadata(modules, _module_inventory_index(modules))


def _module_metadata(
    modules: Mapping[str, LeanModule],
    inventory: _ModuleInventoryIndex,
) -> dict[str, dict[str, Any]]:
    """Build module metadata with inventory classifications already indexed."""

    row_limit = text_declaration_row_limit(modules)
    return {
        name: {
            "path": module.path,
            "lineCount": int(module.line_count),
            "tags": list(module.tags),
            "roles": list(inventory.roles[name]),
            "facadeSubtype": inventory.facade_subtypes[name],
            "declarationCount": len(module.declarations),
            "declarationAuthority": (
                "lexical_text" if module.declaration_evidence else ""
            ),
            "textDeclarations": text_declaration_rows(module, row_limit),
            "textDeclarationOmittedCount": max(
                0,
                len(module.declaration_evidence) - row_limit,
            ),
            "importCount": len(set(module.imports)),
        }
        for name, module in sorted(modules.items())
    }


def text_declaration_row_limit(
    modules: Mapping[str, LeanModule],
) -> int:
    """Bound inventory-wide lexical detail while retaining every module."""

    total = sum(len(module.declaration_evidence) for module in modules.values())
    if total <= MAX_TEXT_DECLARATION_ROWS:
        return total
    return max(1, MAX_TEXT_DECLARATION_ROWS // max(1, len(modules)))


def text_declaration_rows(
    module: LeanModule,
    limit: int,
) -> list[dict[str, Any]]:
    """Return deterministic bounded lexical declaration evidence."""

    return [
        {
            "id": row.identifier,
            "name": row.name,
            "kind": row.kind,
            "line": row.line,
            "column": row.column,
            "startOffset": row.start_offset,
            "endOffset": row.end_offset,
            "sourceRange": row.source_range,
            "namespaceStack": list(row.namespace_stack),
            "sectionStack": list(row.section_stack),
            "modifiers": list(row.modifiers),
            "privacy": row.privacy,
            "locality": row.locality,
            "candidateName": row.candidate_name,
            "candidateStatus": row.candidate_status,
            "blockStartOffset": row.block_start_offset,
            "blockEndOffset": row.block_end_offset,
            "normalizedBlockSha256": row.normalized_block_sha256,
            "blockNormalizationVersion": row.block_normalization_version,
            "authority": row.authority,
            "confidence": row.confidence,
            "nonclaim": row.nonclaim,
        }
        for row in module.declaration_evidence[:limit]
    ]


def text_declaration_summary(
    metadata: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Report the complete count and bounded evidence-row population."""

    total = sum(int(row.get("declarationCount", 0)) for row in metadata.values())
    included = sum(len(row.get("textDeclarations", [])) for row in metadata.values())
    return {
        "total": total,
        "included": included,
        "omitted": max(0, total - included),
        "truncated": included < total,
        "limit": MAX_TEXT_DECLARATION_ROWS,
        "authority": "lexical_text",
        "nonclaim": (
            "Counts cover the selected lexical inventory; bounded detail rows "
            "are not a complete Lean parse or elaboration result."
        ),
    }


def module_count_with_tag(modules: Mapping[str, LeanModule], tag: str) -> int:
    """Return how many modules carry one source-level tag."""

    return sum(1 for module in modules.values() if tag in module.tags)


def top_large_modules(
    modules: Mapping[str, LeanModule],
    *,
    excluded_tags: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Return the largest source files by line count."""

    return [
        {
            "module": module.name,
            "path": module.path,
            "lineCount": int(module.line_count),
            "tags": list(module.tags),
        }
        for module in sorted(
            (
                module
                for module in modules.values()
                if module.line_count > 0 and not has_excluded_tag(module, excluded_tags)
            ),
            key=lambda item: (item.line_count, item.name),
            reverse=True,
        )[:MAX_LARGE_MODULE_ROWS]
    ]


def duplicate_imports(modules: Mapping[str, LeanModule]) -> list[dict[str, Any]]:
    """Return repeated import targets with line-level evidence."""

    rows = [
        duplicate_import_row(module, target, sites)
        for module in sorted(modules.values(), key=lambda item: item.name)
        for target, sites in duplicate_import_sites(module).items()
    ]
    return sorted(
        rows, key=lambda row: (-int(row["count"]), row["module"], row["target"])
    )


def duplicate_import_row(
    module: LeanModule,
    target: str,
    sites: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one duplicate-import report row."""

    return {
        "module": module.name,
        "path": module.path,
        "target": target,
        "count": len(sites),
        "generated": "generated" in module.tags,
        "generatorFamily": generator_family(module),
        "lines": [site["line"] for site in sites if site.get("line") is not None],
        "importTexts": [site["importText"] for site in sites if site.get("importText")],
        "suggestedAction": "remove repeated import lines or fix the generator to emit each import once",
    }


def duplicate_import_family_summary(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group duplicate import rows by generated family and target."""

    grouped: dict[tuple[str, str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("generatorFamily", "")),
            str(row.get("target", "")),
            bool(row.get("generated", False)),
        )
        grouped[key].append(row)
    return [
        {
            "generatorFamily": family,
            "target": target,
            "generated": generated,
            "duplicateModuleCount": len(items),
            "sampleModules": [str(item["module"]) for item in items[:5]],
        }
        for (family, target, generated), items in sorted(
            grouped.items(),
            key=lambda item: (-len(item[1]), item[0][0], item[0][1]),
        )
    ]


def duplicate_import_sites(module: LeanModule) -> dict[str, list[dict[str, Any]]]:
    """Group import sites by target when the same target appears repeatedly."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for site in module.import_sites:
        grouped[site.module].append(
            {
                "line": site.line,
                "importText": site.text or "",
            }
        )
    if not grouped:
        for target in module.imports:
            grouped[target].append({"line": None, "importText": ""})
    return {target: sites for target, sites in grouped.items() if len(sites) > 1}


def import_sites(
    modules: Mapping[str, LeanModule],
    edges: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Return source evidence for known import edges when extraction supplies it."""

    rows: dict[str, dict[str, dict[str, Any]]] = {}
    for source, module in modules.items():
        source_rows = {}
        for site in module.import_sites:
            if site.module not in edges.get(source, ()):
                continue
            source_rows.setdefault(
                site.module,
                {
                    "sourcePath": module.path,
                    "line": site.line,
                    "importText": site.text or "",
                },
            )
        if source_rows:
            rows[source] = source_rows
    return rows


def missing_internal_imports(
    modules: Mapping[str, LeanModule],
    chosen_roots: Sequence[str],
) -> list[dict[str, Any]]:
    """Return imports that look internal but are absent from inventory."""

    project_namespaces = owned_top_namespaces(modules, chosen_roots)
    rows = [
        missing_import_row(module, site)
        for module in sorted(modules.values(), key=lambda item: item.name)
        for site in module.import_sites
        if site.module not in modules
        and import_is_inside_scope(
            module.name,
            site.module,
            chosen_roots,
            project_namespaces=project_namespaces,
        )
    ]
    return sorted(
        rows,
        key=lambda row: (
            row["sourceModule"],
            row["targetModule"],
            row.get("line") or 0,
        ),
    )


def missing_import_row(module: LeanModule, site: Any) -> dict[str, Any]:
    """Build one missing internal import row."""

    return {
        "sourceModule": module.name,
        "sourcePath": module.path,
        "targetModule": site.module,
        "line": site.line,
        "importText": site.text or "",
        "authority": "lexical_text",
        "nonclaim": (
            "Missing conventional source-path evidence only; not a Lean "
            "resolver or compilation diagnostic."
        ),
    }


def lexical_marker_rows(modules: Mapping[str, LeanModule]) -> list[dict[str, Any]]:
    """Return source lexical markers with module context."""

    rows = [
        {
            "module": module.name,
            "path": module.path,
            "kind": marker.kind,
            "line": marker.line,
            "text": marker.text,
            "authority": "lexical_text",
            "nonclaim": (
                "Lexical source marker only; not a Lean-elaborated dependency, "
                "axiom-footprint result, or theorem verdict."
            ),
        }
        for module in sorted(modules.values(), key=lambda item: item.name)
        for marker in module.lexical_markers
    ]
    return sorted(rows, key=lambda row: (row["kind"], row["module"], row["line"]))


def lexical_marker_summary(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count lexical markers by kind."""

    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row["kind"])] += 1
    return dict(sorted(counts.items()))


def cyclic_module_components(
    components: Sequence[Sequence[str]],
    edges: Mapping[str, Sequence[str]],
) -> list[list[str]]:
    """Keep SCCs that represent an actual import cycle."""

    cyclic = [
        list(component)
        for component in components
        if len(component) > 1 or component_has_self_edge(component, edges)
    ]
    return sorted(
        cyclic, key=lambda component: (len(component), component[0]), reverse=True
    )


def component_has_self_edge(
    component: Sequence[str],
    edges: Mapping[str, Sequence[str]],
) -> bool:
    """Return whether an SCC contains a one-module self import."""

    return any(module in edges.get(module, ()) for module in component)


def cycle_summary(cyclic_components: Sequence[Sequence[str]]) -> dict[str, Any]:
    """Render cycle data without exposing the full SCC list by default."""

    return {
        "cyclic_component_count": len(cyclic_components),
        "largest_cyclic_component_size": len(cyclic_components[0])
        if cyclic_components
        else 0,
        "top_cyclic_components": [
            {"size": len(component), "sample_modules": list(component)[:12]}
            for component in cyclic_components[:10]
        ],
    }


def widest_layers(layer_widths: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the widest topological layers for report triage."""

    return sorted(
        layer_widths,
        key=lambda item: (item["width"], -item["rank"]),
        reverse=True,
    )[:10]


def known_roots(
    chosen_roots: Sequence[str],
    modules: Mapping[str, LeanModule],
) -> tuple[str, ...]:
    """Discard requested roots that are outside the discovered inventory."""

    return tuple(root for root in chosen_roots if root in modules)


def reachability_summary(
    modules: Mapping[str, LeanModule],
    edges: Mapping[str, Sequence[str]],
    chosen_roots: Sequence[str],
) -> dict[str, Any]:
    """Summarize modules not reached by following import edges from roots."""

    roots = tuple(chosen_roots)
    if not roots:
        return {}
    unreachable = sorted(
        name for name in modules if name not in reachable_modules(edges, roots)
    )
    return {
        "chosen_roots": list(chosen_roots),
        "source_modules_not_reachable_from_chosen_roots": unreachable[:50],
        "source_modules_not_reachable_from_chosen_roots_count": len(unreachable),
    }


def reverse_module_edges(
    module_names: Sequence[str],
    edges: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    """Return imported-module -> importer edges for fan-in reporting."""

    reverse_edges = {module: [] for module in module_names}
    for source, targets in edges.items():
        for target in targets:
            if target in reverse_edges:
                reverse_edges[target].append(source)
    for sources in reverse_edges.values():
        sources.sort()
    return reverse_edges


def module_ranks(
    module_names: Sequence[str],
    edges: Mapping[str, Sequence[str]],
) -> dict[str, int]:
    """Assign dependency depth ranks for an acyclic importer-to-import graph."""

    indegree_work = initial_indegree(module_names, edges)
    queue: deque[str] = deque(zero_indegree_modules(indegree_work))
    ranks: dict[str, int] = {}
    while queue:
        module = queue.popleft()
        rank = ranks.setdefault(module, 0)
        update_target_ranks(module, rank, edges, indegree_work, ranks, queue)
    return ranks


def initial_indegree(
    module_names: Sequence[str],
    edges: Mapping[str, Sequence[str]],
) -> dict[str, int]:
    """Compute Kahn-style indegrees for importer-to-imported edges."""

    indegree = {module: 0 for module in module_names}
    for target in (target for targets in edges.values() for target in targets):
        if target in indegree:
            indegree[target] += 1
    return indegree


def zero_indegree_modules(indegree: Mapping[str, int]) -> list[str]:
    """Return rank-zero modules for topological layering."""

    return sorted(module for module, count in indegree.items() if count == 0)


def update_target_ranks(
    module: str,
    rank: int,
    edges: Mapping[str, Sequence[str]],
    indegree_work: dict[str, int],
    ranks: dict[str, int],
    queue: deque[str],
) -> None:
    """Propagate one module's rank to its imported targets."""

    for target in edges.get(module, ()):
        if target in indegree_work:
            decrement_indegree(target, rank, indegree_work, ranks, queue)


def decrement_indegree(
    target: str,
    rank: int,
    indegree_work: dict[str, int],
    ranks: dict[str, int],
    queue: deque[str],
) -> None:
    """Update one target during topological rank propagation."""

    ranks[target] = max(ranks.get(target, 0), rank + 1)
    indegree_work[target] -= 1
    if indegree_work[target] == 0:
        queue.append(target)


def summarize_layers(ranks: Mapping[str, int]) -> list[dict[str, Any]]:
    """Group module ranks into compact report rows."""

    by_rank: dict[int, list[str]] = defaultdict(list)
    for module, rank in ranks.items():
        by_rank[rank].append(module)
    return [
        {
            "rank": rank,
            "width": len(sorted_modules),
            "sample_modules": sorted_modules[:12],
        }
        for rank, modules in sorted(by_rank.items())
        for sorted_modules in [sorted(modules)]
    ]


def root_like_modules(reverse_edges: Mapping[str, Sequence[str]]) -> list[str]:
    """Return modules with no known importers in the discovered inventory."""

    return sorted(module for module, sources in reverse_edges.items() if not sources)


def facade_modules(modules: Mapping[str, LeanModule]) -> list[str]:
    """Return modules classified as facade-like."""

    return _facade_modules(_module_inventory_index(modules))


def top_facade_like_modules(modules: Mapping[str, LeanModule]) -> list[dict[str, Any]]:
    """Return facade-like modules with subtype and import breadth."""

    return _top_facade_like_modules(modules, _module_inventory_index(modules))


def facade_subtype(module: LeanModule, modules: Mapping[str, LeanModule]) -> str:
    """Return a generic facade subtype or an empty string."""

    import_count = len(set(module.imports))
    return _facade_subtype(
        module,
        import_count=import_count,
        has_namespace_children=(
            import_count >= 5 and has_namespace_children(module.name, modules)
        ),
    )


def has_namespace_children(module: str, modules: Mapping[str, LeanModule]) -> bool:
    """Return whether `module` has discovered namespace children."""

    prefix = f"{module}."
    return any(name.startswith(prefix) for name in modules)


def facade_subtype_summary(modules: Mapping[str, LeanModule]) -> dict[str, int]:
    """Count facade-like modules by subtype."""

    return _facade_subtype_summary(_module_inventory_index(modules))


def module_roles(
    module: LeanModule, modules: Mapping[str, LeanModule]
) -> tuple[str, ...]:
    """Return structural roles inferred from module inventory."""

    roles: list[str] = []
    subtype = facade_subtype(module, modules)
    if subtype:
        roles.append("facade")
        roles.append(subtype)
    return tuple(roles)


def reachable_modules(
    edges: Mapping[str, Sequence[str]],
    roots: Sequence[str],
) -> set[str]:
    """Follow outgoing import edges from selected roots."""

    reached: set[str] = set()
    queue: deque[str] = deque(sorted(roots))
    while queue:
        module = queue.popleft()
        if module in reached:
            continue
        reached.add(module)
        for target in edges.get(module, ()):
            if target not in reached:
                queue.append(target)
    return reached


def root_direct_import_closures(
    edges: Mapping[str, Sequence[str]],
    roots: Sequence[str],
) -> list[dict[str, Any]]:
    """Summarize reachable closure size for each direct root import."""

    rows = [
        direct_import_closure_row(root, direct_import, edges)
        for root in roots
        for direct_import in edges.get(root, ())
    ]
    return sorted(
        rows,
        key=lambda row: (
            -row["reachable_module_count"],
            row["root"],
            row["direct_import"],
        ),
    )[:30]


def direct_import_closure_row(
    root: str,
    direct_import: str,
    edges: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    """Build one direct-import closure row."""

    reachable = sorted(reachable_modules(edges, (direct_import,)))
    return {
        "root": root,
        "direct_import": direct_import,
        "reachable_module_count": len(reachable),
        "sample_modules": reachable[:12],
    }


def top_fan_in(
    modules: Mapping[str, LeanModule],
    reverse_edges: Mapping[str, Sequence[str]],
    *,
    included_tags: Sequence[str] = (),
    excluded_tags: Sequence[str] = (),
    included_importer_tags: Sequence[str] = (),
    excluded_importer_tags: Sequence[str] = (),
    population: str = "all_importers_to_all_targets",
) -> list[dict[str, Any]]:
    """Return modules most often imported by other discovered modules."""

    return _top_fan_in(
        modules,
        reverse_edges,
        _module_inventory_index(modules),
        included_tags=included_tags,
        excluded_tags=excluded_tags,
        included_importer_tags=included_importer_tags,
        excluded_importer_tags=excluded_importer_tags,
        population=population,
    )


def fan_in_importers(
    target: str,
    modules: Mapping[str, LeanModule],
    reverse_edges: Mapping[str, Sequence[str]],
    *,
    included_tags: Sequence[str],
    excluded_tags: Sequence[str],
) -> list[str]:
    """Return importers accepted by an explicitly named fan-in population."""

    return sorted(
        importer
        for importer in reverse_edges.get(target, ())
        if importer in modules
        and has_included_tag(modules[importer], included_tags)
        and not has_excluded_tag(modules[importer], excluded_tags)
    )


def top_fan_out(
    modules: Mapping[str, LeanModule],
    edges: Mapping[str, Sequence[str]],
    *,
    excluded_tags: Sequence[str] = (),
    included_roles: Sequence[str] = (),
    excluded_roles: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Return modules with the broadest direct import surface."""

    return _top_fan_out(
        modules,
        edges,
        _module_inventory_index(modules),
        excluded_tags=excluded_tags,
        included_roles=included_roles,
        excluded_roles=excluded_roles,
    )


def modules_matching_filters(
    modules: Mapping[str, LeanModule],
    *,
    included_tags: Sequence[str] = (),
    excluded_tags: Sequence[str] = (),
    included_roles: Sequence[str] = (),
    excluded_roles: Sequence[str] = (),
) -> list[str]:
    """Return module names accepted by tag and structural-role filters."""

    return _modules_matching_filters(
        _module_inventory_index(modules),
        included_tags=included_tags,
        excluded_tags=excluded_tags,
        included_roles=included_roles,
        excluded_roles=excluded_roles,
    )


def has_excluded_tag(module: LeanModule, excluded_tags: Sequence[str]) -> bool:
    """Return whether one module has any excluded source-level tag."""

    return bool(set(module.tags) & set(excluded_tags))


def has_included_tag(module: LeanModule, included_tags: Sequence[str]) -> bool:
    """Return whether one module passes optional source-tag inclusion."""

    if not included_tags:
        return True
    return bool(set(module.tags) & set(included_tags))


def has_included_role(
    module: LeanModule,
    modules: Mapping[str, LeanModule],
    included_roles: Sequence[str],
) -> bool:
    """Return whether one module passes optional role inclusion."""

    if not included_roles:
        return True
    return bool(set(module_roles(module, modules)) & set(included_roles))


def has_excluded_role(
    module: LeanModule,
    modules: Mapping[str, LeanModule],
    excluded_roles: Sequence[str],
) -> bool:
    """Return whether one module carries any excluded structural role."""

    return bool(set(module_roles(module, modules)) & set(excluded_roles))


def tarjan_scc(
    nodes: Sequence[str], edges: Mapping[str, Sequence[str]]
) -> list[list[str]]:
    """Compute strongly connected components for import-cycle detection."""

    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in edges.get(node, ()):
            if target not in indexes:
                strongconnect(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])

        if lowlinks[node] != indexes[node]:
            return
        component: list[str] = []
        while True:
            target = stack.pop()
            on_stack.remove(target)
            component.append(target)
            if target == node:
                break
        components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indexes:
            strongconnect(node)
    return components
