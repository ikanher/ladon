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
    module_names = sorted(modules)
    edges = {
        name: sorted(imported for imported in module.imports if imported in modules)
        for name, module in modules.items()
    }
    reverse_edges = reverse_module_edges(module_names, edges)
    components = tarjan_scc(module_names, edges)
    cyclic_components = [
        component
        for component in components
        if len(component) > 1 or any(module in edges.get(module, []) for module in component)
    ]
    cyclic_components.sort(key=lambda component: (len(component), component[0]), reverse=True)
    acyclic = not cyclic_components
    ranks = module_ranks(module_names, edges) if acyclic else {}
    layer_widths = summarize_layers(ranks)
    chosen_roots = tuple(root for root in chosen_roots if root in modules)
    reachable = reachable_modules(edges, chosen_roots or tuple(root_like_modules(reverse_edges)))
    not_reachable = sorted(name for name in modules if name not in reachable)

    return {
        "scope": "repo_inventory",
        "method": "repo_wide_module_import_dag",
        "module_count": len(module_names),
        "edge_count": sum(len(targets) for targets in edges.values()),
        "acyclic": acyclic,
        "scc_count": len(components),
        "cyclic_component_count": len(cyclic_components),
        "largest_cyclic_component_size": len(cyclic_components[0]) if cyclic_components else 0,
        "top_cyclic_components": [
            {"size": len(component), "sample_modules": component[:12]}
            for component in cyclic_components[:10]
        ],
        "max_rank": max(ranks.values(), default=0),
        "topological_layer_count": len(layer_widths),
        "layer_widths": layer_widths[:80],
        "widest_layers": sorted(
            layer_widths,
            key=lambda item: (item["width"], -item["rank"]),
            reverse=True,
        )[:10],
        "top_fan_in": top_fan_in(modules, reverse_edges),
        "top_fan_out": top_fan_out(modules, edges),
        "root_like_modules": root_like_modules(reverse_edges)[:20],
        "root_like_module_count": len(root_like_modules(reverse_edges)),
        "facade_modules": facade_modules(modules)[:20],
        "facade_module_count": len(facade_modules(modules)),
        "chosen_roots": list(chosen_roots),
        "source_modules_not_reachable_from_chosen_roots": not_reachable[:50],
        "source_modules_not_reachable_from_chosen_roots_count": len(not_reachable),
        "edges": edges,
    }


def reverse_module_edges(
    module_names: Sequence[str],
    edges: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
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
    indegree = {module: 0 for module in module_names}
    for targets in edges.values():
        for target in targets:
            if target in indegree:
                indegree[target] += 1
    queue: deque[str] = deque(sorted(module for module, count in indegree.items() if count == 0))
    indegree_work = dict(indegree)
    ranks: dict[str, int] = {}
    while queue:
        module = queue.popleft()
        rank = ranks.setdefault(module, 0)
        for target in edges.get(module, ()):
            if target not in indegree_work:
                continue
            ranks[target] = max(ranks.get(target, 0), rank + 1)
            indegree_work[target] -= 1
            if indegree_work[target] == 0:
                queue.append(target)
    return ranks


def summarize_layers(ranks: Mapping[str, int]) -> list[dict[str, Any]]:
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
    return sorted(module for module, sources in reverse_edges.items() if not sources)


def facade_modules(modules: Mapping[str, LeanModule]) -> list[str]:
    return sorted(
        name
        for name, module in modules.items()
        if module.imports and not module.declarations
    )


def reachable_modules(
    edges: Mapping[str, Sequence[str]],
    roots: Sequence[str],
) -> set[str]:
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


def top_fan_in(
    modules: Mapping[str, LeanModule],
    reverse_edges: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
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
