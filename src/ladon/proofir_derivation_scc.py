"""Bounded SCC projection for validated ProofIR derivation artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.proofir_derivation import (
    DerivationQueryBounds,
    RefKey,
    _Budget,
    _Graph,
    _invalid,
    _InvalidGraph,
    _key,
    _Prepared,
    _ref,
    _result,
)


def analyze_sccs(
    artifact: Any,
    *,
    bounds: DerivationQueryBounds | None = None,
) -> dict[str, Any]:
    """Expose exact recursive components without fixed-point or checker claims."""

    prepared = _prepare_scc(artifact, bounds or DerivationQueryBounds())
    if prepared.error:
        return _invalid(prepared, "scc-analysis")
    budget = _Budget(prepared.bounds)
    rows = _bounded_component_rows(prepared.graph, budget)
    budget.counts["returnedRows"] = len(rows)
    recursive = bool(prepared.graph.recursive_components)
    status = _scc_status(recursive, bool(budget.truncations))
    return _result(
        prepared,
        "scc-analysis",
        budget,
        status,
        {"recursive": recursive, "components": rows},
        complete=not budget.truncations,
    )


def _prepare_scc(artifact: Any, bounds: DerivationQueryBounds) -> _Prepared:
    """Validate one derivation or return an attributable invalid query state."""

    try:
        graph = _Graph.build(artifact)
    except _InvalidGraph as error:
        raw = _raw_artifact(artifact)
        return _Prepared(
            _empty_graph(raw),
            ("derivation", ""),
            frozenset(),
            bounds,
            error.diagnostic,
        )
    raw = _raw_artifact(artifact)
    return _Prepared(
        graph,
        ("derivation", str(raw["payload"]["derivationId"])),
        frozenset(),
        bounds,
    )


def _raw_artifact(artifact: Any) -> Mapping[str, Any]:
    """Recover a raw mapping from either checked or unchecked input."""

    raw = artifact.payload if hasattr(artifact, "payload") else artifact
    return raw if isinstance(raw, Mapping) else {}


def _empty_graph(raw: Mapping[str, Any]) -> _Graph:
    """Construct identity-only graph context for an invalid result."""

    return _Graph(
        str(raw.get("artifactId", "")),
        str(raw.get("environmentRef", "")),
        frozenset(),
        (),
        {},
        {},
        (),
        {},
    )


def _bounded_component_rows(graph: _Graph, budget: _Budget) -> list[dict[str, Any]]:
    """Return only wholly charged components; never publish a partial SCC."""

    rows: list[dict[str, Any]] = []
    for component in sorted(
        graph.recursive_components, key=lambda row: str(row["componentId"])
    ):
        row = _bounded_component(graph, budget, component)
        if row is None:
            break
        rows.append(row)
    return rows


def _bounded_component(
    graph: _Graph, budget: _Budget, component: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Charge all members and internal edges before constructing one row."""

    members = tuple(sorted(_key(row) for row in component["statementRefs"]))
    if not _charge_members(budget, members):
        return None
    edges = _internal_edges(graph, members)
    if not _charge_edges(budget, edges):
        return None
    return {
        "componentId": component["componentId"],
        "semantics": component["semantics"],
        "statementRefs": [_ref(member) for member in members],
        "internalEdges": [
            {"fromRef": _ref(source), "toRef": _ref(target)} for source, target in edges
        ],
    }


def _charge_members(budget: _Budget, members: tuple[RefKey, ...]) -> bool:
    return all(
        budget.take("maxVisitedRefs", [{"ref": _ref(member)}]) for member in members
    )


def _internal_edges(
    graph: _Graph, members: tuple[RefKey, ...]
) -> tuple[tuple[RefKey, RefKey], ...]:
    member_set = frozenset(members)
    return tuple(
        sorted(
            (source, target)
            for source in members
            for target in graph.dependencies.get(source, ())
            if target in member_set
        )
    )


def _charge_edges(budget: _Budget, edges: tuple[tuple[RefKey, RefKey], ...]) -> bool:
    return all(
        budget.take(
            "maxPremiseSlots", [{"fromRef": _ref(source), "toRef": _ref(target)}]
        )
        for source, target in edges
    )


def _scc_status(recursive: bool, truncated: bool) -> str:
    if truncated:
        return "truncated"
    return "complete" if recursive else "not-recursive"


__all__ = ["analyze_sccs"]
