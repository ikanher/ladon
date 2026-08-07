"""Small deterministic algorithms over already bounded lineage rows.

This module intentionally has no repository, SQLite, or subprocess dependencies.
"""

from __future__ import annotations

from collections.abc import Iterable


class AlgorithmInputError(ValueError):
    """The SQL layer did not establish a safe bounded input."""


def _bounded(nodes: Iterable[str], edges: Iterable[tuple[str, str]], cap: int) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    node_rows = tuple(sorted(set(nodes)))
    edge_rows = tuple(sorted(set(edges)))
    if cap < 1 or len(node_rows) > cap or len(edge_rows) > cap * 4:
        raise AlgorithmInputError("bounded lineage input exceeds established cap")
    if any(source not in node_rows or target not in node_rows for source, target in edge_rows):
        raise AlgorithmInputError("edge endpoint is missing from bounded nodes")
    return node_rows, edge_rows


def compute_dominators(
    nodes: Iterable[str],
    edges: Iterable[tuple[str, str]],
    roots: Iterable[str],
    target: str,
    *,
    cap: int = 5000,
) -> dict[str, object]:
    """Return deterministic mandatory dominators for a bounded directed graph."""
    node_rows, edge_rows = _bounded(nodes, edges, cap)
    root_rows = _validate_roots(roots, node_rows, target)
    predecessors = {node: set() for node in node_rows}
    for source, destination in edge_rows:
        predecessors[destination].add(source)
    universe = set(node_rows)
    dominators = {node: ({node} if node in root_rows else set(universe)) for node in node_rows}
    _iterate_dominators(node_rows, root_rows, predecessors, dominators)
    chain = sorted(dominators[target], key=lambda node: (_distance(node, edge_rows, root_rows), node))
    immediate = chain[-2] if len(chain) > 1 else None
    return {"chain": chain, "immediate": immediate, "dominators": {key: sorted(value) for key, value in dominators.items()}}


def _validate_roots(roots: Iterable[str], nodes: tuple[str, ...], target: str) -> tuple[str, ...]:
    root_rows = tuple(sorted(set(roots)))
    if not root_rows or target not in nodes or any(root not in nodes for root in root_rows):
        raise AlgorithmInputError("roots and target must be bounded graph nodes")
    return root_rows


def _iterate_dominators(nodes: tuple[str, ...], roots: tuple[str, ...], predecessors: dict[str, set[str]], dominators: dict[str, set[str]]) -> None:
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if node in roots:
                continue
            incoming = predecessors[node]
            candidate = {node} | (set.intersection(*(dominators[parent] for parent in incoming)) if incoming else set())
            if candidate != dominators[node]:
                dominators[node] = candidate
                changed = True


def _distance(node: str, edges: tuple[tuple[str, str], ...], roots: tuple[str, ...]) -> int:
    current = set(roots)
    seen = set(current)
    for distance in range(len(edges) + 2):
        if node in current:
            return distance
        current = {target for source, target in edges if source in current and target not in seen}
        seen.update(current)
    return len(edges) + 2


def unfold_tree(
    roots: Iterable[str],
    edges: Iterable[tuple[str, str]],
    *,
    max_depth: int = 32,
    max_nodes: int = 1000,
    max_bytes: int = 1_000_000,
    cap: int = 5000,
) -> dict[str, object]:
    """Unfold a DAG with explicit shared/cycle references and omission records."""
    if max_depth < 1 or max_nodes < 1 or max_bytes < 1:
        raise AlgorithmInputError("tree caps must be positive")
    edge_rows = tuple(sorted(set(edges)))
    node_rows = set(roots) | {item for edge in edge_rows for item in edge}
    node_rows, edge_rows = _bounded(node_rows, edge_rows, cap)
    children = {node: [] for node in node_rows}
    for source, target in edge_rows:
        children[source].append(target)
    for values in children.values():
        values.sort()
    expanded: set[str] = set()
    references: list[dict[str, object]] = []
    omissions: list[dict[str, object]] = []
    rendered_nodes: list[dict[str, object]] = []
    used_bytes = 0

    def visit(node: str, depth: int, path: tuple[str, ...]) -> dict[str, object]:
        nonlocal used_bytes
        if depth > max_depth:
            omissions.append({"kind": "depth", "node": node, "lowerBound": 1})
            return {"node": node, "reference": "depth-cap"}
        if node in path:
            references.append({"node": node, "kind": "cycle"})
            return {"node": node, "reference": "cycle"}
        if node in expanded:
            references.append({"node": node, "kind": "shared"})
            return {"node": node, "reference": "shared"}
        if len(rendered_nodes) >= max_nodes:
            omissions.append({"kind": "nodes", "node": node, "lowerBound": 1})
            return {"node": node, "reference": "node-cap"}
        estimate = len(node) + 32
        if used_bytes + estimate > max_bytes:
            omissions.append({"kind": "bytes", "node": node, "lowerBound": 1})
            return {"node": node, "reference": "byte-cap"}
        expanded.add(node)
        used_bytes += estimate
        rendered_nodes.append({"node": node, "depth": depth})
        return {"node": node, "children": [visit(child, depth + 1, path + (node,)) for child in children[node]]}

    trees = [visit(root, 0, ()) for root in sorted(set(roots))]
    return {"trees": trees, "nodes": rendered_nodes, "references": references, "omissions": omissions, "usedBytes": used_bytes}


__all__ = ["AlgorithmInputError", "compute_dominators", "unfold_tree"]
