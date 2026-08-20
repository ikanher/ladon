"""Small deterministic graph projections used by theorem capsule planning."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ladon.theorem_capsule_models import CapsuleOperationalError


def normalize_helper_nodes(
    helper: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Normalize helper nodes and their complete dependency collections."""

    nodes = helper.get("nodes")
    if not isinstance(nodes, list):
        raise CapsuleOperationalError("Lean theorem nodes are malformed")
    normalized = [_normalize_node(row) for row in nodes]
    return tuple(sorted(normalized, key=lambda row: row["name"]))


def _normalize_node(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        raise CapsuleOperationalError("Lean theorem node is malformed")
    return {
        "name": str(row.get("name")),
        "kind": str(row.get("kind")),
        "ownerModule": str(row.get("ownerModule")),
        "compilerGenerated": bool(row.get("compilerGenerated")),
        "typeFingerprint": str(row.get("typeFingerprint")),
        "valueFingerprint": row.get("valueFingerprint"),
        "declaredAxiom": bool(row.get("declaredAxiom")),
        "unsafe": bool(row.get("unsafe")),
        "typeDependencies": _normalized_dependencies(row.get("typeDependencies")),
        "valueDependencies": _normalized_dependencies(row.get("valueDependencies")),
    }


def _normalized_dependencies(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CapsuleOperationalError("Lean theorem dependencies are malformed")
    rows = []
    for row in value:
        if not isinstance(row, Mapping):
            raise CapsuleOperationalError("Lean theorem dependency is malformed")
        rows.append(
            {
                "name": str(row.get("name")),
                "ownerModule": str(row.get("ownerModule")),
                "kind": str(row.get("kind")),
                "declaredAxiom": bool(row.get("declaredAxiom")),
                "unsafe": bool(row.get("unsafe")),
            }
        )
    return sorted(rows, key=lambda row: (row["name"], row["ownerModule"]))


def semantic_edges(
    nodes: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return deterministic type and value dependency edges."""

    edges = [
        {
            "source": str(node["name"]),
            "target": str(dependency["name"]),
            "kind": kind,
            "targetOwnerModule": str(dependency["ownerModule"]),
            "targetKind": str(dependency["kind"]),
        }
        for node in nodes
        for kind, key in (("type", "typeDependencies"), ("value", "valueDependencies"))
        for dependency in _rows(node[key])
    ]
    return tuple(sorted(edges, key=_edge_key))


def _edge_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["source"]),
        str(row["kind"]),
        str(row["target"]),
        str(row["targetOwnerModule"]),
    )


def semantic_external_frontier(
    nodes: Iterable[Mapping[str, Any]],
    edges: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return typed dependency edges whose target is outside the local closure."""

    names = {str(node["name"]) for node in nodes}
    return tuple(dict(edge) for edge in edges if str(edge["target"]) not in names)


def semantic_components(
    nodes: Iterable[Mapping[str, Any]],
    edges: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Condense the local semantic graph into deterministic SCC evidence."""

    names = tuple(sorted(str(node["name"]) for node in nodes))
    selected = set(names)
    adjacency = {
        name: tuple(sorted(_local_targets(name, edges, selected))) for name in names
    }
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    components: list[tuple[str, ...]] = []
    counter = [0]

    def visit(name: str) -> None:
        index = counter[0]
        counter[0] += 1
        indices[name] = index
        lowlinks[name] = index
        stack.append(name)
        active.add(name)
        for target in adjacency[name]:
            if target not in indices:
                visit(target)
                lowlinks[name] = min(lowlinks[name], lowlinks[target])
            elif target in active:
                lowlinks[name] = min(lowlinks[name], indices[target])
        if lowlinks[name] != indices[name]:
            return
        component = []
        while stack:
            target = stack.pop()
            active.remove(target)
            component.append(target)
            if target == name:
                break
        components.append(tuple(sorted(component)))

    for name in names:
        if name not in indices:
            visit(name)
    return tuple(_component_row(component, adjacency) for component in sorted(components))


def _local_targets(
    name: str,
    edges: Iterable[Mapping[str, Any]],
    selected: set[str],
) -> set[str]:
    return {
        str(edge["target"])
        for edge in edges
        if edge.get("source") == name and str(edge.get("target")) in selected
    }


def _component_row(
    component: tuple[str, ...],
    adjacency: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    return {
        "component": component,
        "members": list(component),
        "cyclic": len(component) > 1 or component[0] in adjacency[component[0]],
    }


def trust_frontier(
    nodes: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return explicit axiom and unsafe facts at the capsule boundary."""

    facts: set[tuple[str, str, str]] = set()
    for node in nodes:
        name = str(node["name"])
        if node.get("declaredAxiom"):
            facts.add(("declared_axiom", "declaration", name))
        if node.get("unsafe"):
            facts.add(("unsafe", "declaration", name))
        for scope, key in (("type", "typeDependencies"), ("value", "valueDependencies")):
            _add_dependency_trust(facts, scope, _rows(node[key]))
    return tuple(
        {"kind": kind, "scope": scope, "target": target}
        for kind, scope, target in sorted(facts)
    )


def _add_dependency_trust(
    facts: set[tuple[str, str, str]],
    scope: str,
    dependencies: Iterable[Mapping[str, Any]],
) -> None:
    for dependency in dependencies:
        name = str(dependency["name"])
        if dependency.get("declaredAxiom"):
            kind = "sorryAx" if name.endswith("sorryAx") else "axiom_reference"
            facts.add((kind, scope, name))
        if dependency.get("unsafe"):
            facts.add(("unsafe_reference", scope, name))


def _rows(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise CapsuleOperationalError("theorem capsule row collection is malformed")
    return tuple(value)


__all__ = [
    "normalize_helper_nodes",
    "semantic_components",
    "semantic_edges",
    "semantic_external_frontier",
    "trust_frontier",
]
