"""Deterministic, bounded graph primitives for proof-engineering projections."""

from __future__ import annotations

from collections import deque
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from typing import TypeVar

Node = TypeVar("Node")


@dataclass(frozen=True)
class GraphRequest:
    """A finite graph request with explicit safety caps."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    roots: tuple[str, ...] = ()
    max_depth: int = 64
    max_paths: int = 100
    max_output_nodes: int = 10_000


@dataclass(frozen=True)
class GraphResult:
    """Normalized adjacency plus explicit omissions and stable integer IDs."""

    nodes: tuple[str, ...]
    node_ids: Mapping[str, int]
    forward: Mapping[str, tuple[str, ...]]
    reverse: Mapping[str, tuple[str, ...]]
    omissions: tuple[dict[str, str], ...] = ()


def normalize_graph(request: GraphRequest) -> GraphResult:
    """Normalize malformed edges, duplicate references, and deterministic order."""

    _validate_caps(request)
    nodes = tuple(sorted(dict.fromkeys(request.nodes)))
    known = set(nodes)
    forward: dict[str, set[str]] = {node: set() for node in nodes}
    reverse: dict[str, set[str]] = {node: set() for node in nodes}
    omissions: list[dict[str, str]] = []
    for source, target in request.edges:
        if source not in known or target not in known:
            omissions.append(
                {
                    "kind": "edge",
                    "subject": f"{source}->{target}",
                    "reason": "endpoint_not_indexed",
                }
            )
            continue
        forward[source].add(target)
        reverse[target].add(source)
    return GraphResult(
        nodes=nodes,
        node_ids={node: index for index, node in enumerate(nodes)},
        forward={node: tuple(sorted(targets)) for node, targets in forward.items()},
        reverse={node: tuple(sorted(sources)) for node, sources in reverse.items()},
        omissions=tuple(omissions),
    )


def bounded_bfs(
    graph: GraphResult,
    roots: Iterable[str],
    *,
    reverse: bool = False,
    max_depth: int = 64,
) -> tuple[str, ...]:
    """Expand a bounded frontier once, preserving stable breadth-first order."""

    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    adjacency = graph.reverse if reverse else graph.forward
    queue = deque((root, 0) for root in sorted(set(roots)) if root in graph.node_ids)
    seen: set[str] = set()
    result: list[str] = []
    while queue:
        node, depth = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        result.append(node)
        if depth < max_depth:
            queue.extend((target, depth + 1) for target in adjacency.get(node, ()))
    return tuple(result)


def bounded_paths(
    graph: GraphResult,
    start: str,
    end: str | None = None,
    *,
    reverse: bool = False,
    max_depth: int = 64,
    max_paths: int = 100,
) -> tuple[tuple[str, ...], ...]:
    """Enumerate cycle-safe paths with deterministic depth/path ordering."""

    _validate_path_caps(max_depth, max_paths)
    if start not in graph.node_ids:
        return ()
    adjacency = graph.reverse if reverse else graph.forward
    found = _enumerate_paths(adjacency, start, end, max_depth, max_paths)
    return tuple(sorted(found, key=lambda path: (len(path), path))[:max_paths])


def strongly_connected_components(graph: GraphResult) -> tuple[tuple[str, ...], ...]:
    """Return stable SCCs using an iterative two-pass reachability algorithm."""

    return strongly_connected_components_from_adjacency(graph.forward)


def strongly_connected_components_from_adjacency(
    adjacency: Mapping[Node, Collection[Node]],
) -> tuple[tuple[Node, ...], ...]:
    """Return deterministic iterative Kosaraju components for opaque nodes."""

    nodes = sorted(set(adjacency).union(*(set(rows) for rows in adjacency.values())))
    finished = _adjacency_finish_order(nodes, adjacency)
    reverse = _reverse_adjacency(nodes, adjacency)
    return _reverse_components(finished, reverse)


def _adjacency_finish_order(
    nodes: list[Node], adjacency: Mapping[Node, Collection[Node]]
) -> list[Node]:
    """Compute deterministic DFS finish order without recursive calls."""

    visited: set[Node] = set()
    finished: list[Node] = []
    for node in nodes:
        if node in visited:
            continue
        stack: list[tuple[Node, bool]] = [(node, False)]
        while stack:
            current, expanded = stack.pop()
            if expanded:
                finished.append(current)
                continue
            if current in visited:
                continue
            visited.add(current)
            stack.append((current, True))
            stack.extend(
                (target, False)
                for target in sorted(adjacency.get(current, ()), reverse=True)
                if target not in visited
            )
    return finished


def _reverse_adjacency(
    nodes: list[Node], adjacency: Mapping[Node, Collection[Node]]
) -> dict[Node, set[Node]]:
    """Build the complete reverse adjacency, including isolated nodes."""

    reverse: dict[Node, set[Node]] = {node: set() for node in nodes}
    for source, targets in adjacency.items():
        for target in targets:
            reverse[target].add(source)
    return reverse


def _reverse_components(
    finished: list[Node], reverse: Mapping[Node, Collection[Node]]
) -> tuple[tuple[Node, ...], ...]:
    """Collect components in reverse finish order with an iterative DFS."""

    assigned: set[Node] = set()
    components: list[tuple[Node, ...]] = []
    for node in reversed(finished):
        if node in assigned:
            continue
        component: list[Node] = []
        stack = [node]
        while stack:
            current = stack.pop()
            if current in assigned:
                continue
            assigned.add(current)
            component.append(current)
            stack.extend(
                source
                for source in sorted(reverse[current], reverse=True)
                if source not in assigned
            )
        components.append(tuple(sorted(component)))
    return tuple(sorted(components))


def cyclic_components(
    adjacency: Mapping[Node, Collection[Node]],
) -> tuple[tuple[Node, ...], ...]:
    """Return SCCs containing a cycle, including explicit self-loops."""

    return tuple(
        component
        for component in strongly_connected_components_from_adjacency(adjacency)
        if len(component) > 1 or component[0] in adjacency.get(component[0], ())
    )


def unfold_dag(graph: GraphResult) -> dict[str, object]:
    """Collapse SCCs while retaining shared-node and cycle reference metadata."""

    components = strongly_connected_components(graph)
    owner = {
        node: index for index, component in enumerate(components) for node in component
    }
    edges = _component_edges(graph, owner)
    references = _component_references(graph, components, owner)
    return {
        "components": [list(component) for component in components],
        "edges": [list(edge) for edge in edges],
        "references": references,
    }


def _component_edges(
    graph: GraphResult, owner: Mapping[str, int]
) -> list[tuple[int, int]]:
    return sorted(
        {
            (owner[source], owner[target])
            for source, targets in graph.forward.items()
            for target in targets
            if owner[source] != owner[target]
        }
    )


def _component_references(
    graph: GraphResult,
    components: tuple[tuple[str, ...], ...],
    owner: Mapping[str, int],
) -> list[dict[str, object]]:
    return [
        {
            "node": node,
            "component": owner[node],
            "kind": "cycle"
            if len(components[owner[node]]) > 1 or node in graph.forward[node]
            else "shared",
        }
        for node in graph.nodes
        if len(components[owner[node]]) > 1 or node in graph.forward[node]
    ]


def dominators(
    graph: GraphResult, roots: Iterable[str]
) -> Mapping[str, frozenset[str]]:
    """Compute dominators with explicit multiple-root and unreachable semantics."""

    roots_set = {root for root in roots if root in graph.node_ids}
    reachable = set(bounded_bfs(graph, roots_set, max_depth=len(graph.nodes)))
    result = {node: frozenset() for node in graph.nodes if node not in reachable}
    dom = {
        node: (frozenset({node}) if node in roots_set else frozenset(reachable))
        for node in reachable
    }
    _iterate_dominators(graph, reachable, roots_set, dom)
    result.update(dom)
    return result


def brute_force_dominators(
    graph: GraphResult, roots: Iterable[str]
) -> Mapping[str, frozenset[str]]:
    """Small-graph oracle retained for differential tests."""

    roots_set = {root for root in roots if root in graph.node_ids}
    reachable = set(bounded_bfs(graph, roots_set, max_depth=len(graph.nodes)))
    result: dict[str, frozenset[str]] = {}
    for node in graph.nodes:
        if node not in reachable:
            result[node] = frozenset()
            continue
        result[node] = frozenset(
            candidate
            for candidate in reachable
            if _dominates(graph, roots_set, candidate, node)
        )
    return result


def _dominates(
    graph: GraphResult, roots: set[str], candidate: str, target: str
) -> bool:
    if target in roots:
        return candidate == target or candidate in roots
    paths = tuple(
        path
        for root in sorted(roots)
        for path in bounded_paths(
            graph, root, target, max_depth=len(graph.nodes), max_paths=10_000
        )
    )
    return bool(paths) and all(candidate in path for path in paths)


def _reachable(graph: GraphResult, start: str, target: str) -> bool:
    return target in bounded_bfs(graph, (start,), max_depth=len(graph.nodes))


def _validate_caps(request: GraphRequest) -> None:
    if min(request.max_depth, request.max_paths, request.max_output_nodes) < 1:
        raise ValueError("graph caps must be positive")


def _validate_path_caps(max_depth: int, max_paths: int) -> None:
    if min(max_depth, max_paths) < 1:
        raise ValueError("path bounds must be positive")


def _enumerate_paths(
    adjacency: Mapping[str, tuple[str, ...]],
    start: str,
    end: str | None,
    max_depth: int,
    max_paths: int,
) -> list[tuple[str, ...]]:
    found: list[tuple[str, ...]] = []
    stack: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
    while stack and len(found) <= max_paths:
        node, path = stack.pop()
        if end is None or node == end:
            found.append(path)
        if len(path) - 1 < max_depth:
            stack.extend(
                (target, path + (target,))
                for target in reversed(adjacency.get(node, ()))
                if target not in path
            )
    return found


def _iterate_dominators(
    graph: GraphResult,
    reachable: set[str],
    roots: set[str],
    dom: dict[str, frozenset[str]],
) -> None:
    changed = True
    while changed:
        changed = False
        for node in sorted(reachable - roots):
            predecessors = [pred for pred in graph.reverse[node] if pred in reachable]
            intersection = (
                set.intersection(*(set(dom[pred]) for pred in predecessors))
                if predecessors
                else set()
            )
            candidate = frozenset({node} | intersection)
            if candidate != dom[node]:
                dom[node] = candidate
                changed = True


__all__ = [
    "GraphRequest",
    "GraphResult",
    "bounded_bfs",
    "bounded_paths",
    "brute_force_dominators",
    "cyclic_components",
    "dominators",
    "normalize_graph",
    "strongly_connected_components",
    "strongly_connected_components_from_adjacency",
    "unfold_dag",
]
