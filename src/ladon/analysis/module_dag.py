"""Pure module-import DAG analysis for Ladon's clean core.

Edges point from an importing module to the modules it imports. That direction
matches the way a reviewer reads dependency pull: root modules reach their
implementation dependencies by following outgoing edges.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.ir import LeanModule


def summarize_module_dag(
    modules: Mapping[str, LeanModule],
    *,
    chosen_roots: Sequence[str] = (),
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
    reachability = reachability_summary(modules, edges, reverse_edges, selected_roots)

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
        "top_fan_in": top_fan_in(modules, reverse_edges),
        "top_fan_out": top_fan_out(modules, edges),
        "root_like_modules": root_like_modules(reverse_edges)[:20],
        "root_like_module_count": len(root_like_modules(reverse_edges)),
        "facade_modules": facade_modules(modules)[:20],
        "facade_module_count": len(facade_modules(modules)),
        "root_direct_import_closures": root_direct_import_closures(edges, selected_roots),
        **reachability,
        "edges": edges,
    }


def module_edges(modules: Mapping[str, LeanModule]) -> dict[str, list[str]]:
    """Return importer -> imported-module edges restricted to known modules."""

    return {
        name: sorted(imported for imported in module.imports if imported in modules)
        for name, module in modules.items()
    }


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
    return sorted(cyclic, key=lambda component: (len(component), component[0]), reverse=True)


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
        "largest_cyclic_component_size": len(cyclic_components[0]) if cyclic_components else 0,
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
    reverse_edges: Mapping[str, Sequence[str]],
    chosen_roots: Sequence[str],
) -> dict[str, Any]:
    """Summarize modules not reached by following import edges from roots."""

    roots = tuple(chosen_roots) or tuple(root_like_modules(reverse_edges))
    unreachable = sorted(name for name in modules if name not in reachable_modules(edges, roots))
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
    """Return modules that import others but declare no local names."""

    return sorted(
        name
        for name, module in modules.items()
        if module.imports and not module.declarations
    )


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
        key=lambda row: (-row["reachable_module_count"], row["root"], row["direct_import"]),
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
) -> list[dict[str, Any]]:
    """Return modules most often imported by other discovered modules."""

    return [
        {
            "module": name,
            "path": modules[name].path,
            "fan_in": len(reverse_edges.get(name, ())),
            "sample_importers": list(reverse_edges.get(name, ()))[:12],
        }
        for name in sorted(
            modules,
            key=lambda item: (len(reverse_edges.get(item, ())), item),
            reverse=True,
        )[:15]
    ]


def top_fan_out(
    modules: Mapping[str, LeanModule],
    edges: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Return modules with the broadest direct import surface."""

    return [
        {
            "module": name,
            "path": modules[name].path,
            "fan_out": len(edges.get(name, ())),
            "sample_imports": list(edges.get(name, ()))[:12],
        }
        for name in sorted(
            modules,
            key=lambda item: (len(edges.get(item, ())), item),
            reverse=True,
        )[:15]
    ]


def tarjan_scc(nodes: Sequence[str], edges: Mapping[str, Sequence[str]]) -> list[list[str]]:
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
