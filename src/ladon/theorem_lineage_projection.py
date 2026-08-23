"""Bounded render-neutral projections over theorem-lineage query results."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from ladon.theorem_lineage_algorithms import (
    AlgorithmInputError,
    compute_dominators,
    unfold_tree,
)
from ladon.theorem_lineage_query import LineageQuery, query_lineage
from ladon.theorem_lineage_store import LineageIdentity


class TheoremLineageProjectionError(ValueError):
    """Projection input is unavailable or exceeds declared bounds."""


@dataclass(frozen=True)
class ProjectionQuery:
    lineage: LineageQuery
    view: str = "routes"
    max_algorithm_nodes: int = 5000
    max_tree_depth: int = 32
    max_tree_bytes: int = 1_000_000
    max_dominator_rows: int = 100

    def __post_init__(self) -> None:
        if self.view not in {"routes", "graph", "tree", "bottlenecks"}:
            raise TheoremLineageProjectionError("unsupported projection view")
        if self.max_algorithm_nodes < 1:
            raise TheoremLineageProjectionError("algorithm node cap must be positive")
        if self.max_dominator_rows < 1:
            raise TheoremLineageProjectionError("dominator summary cap must be positive")


def project_lineage(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    query: ProjectionQuery,
) -> dict[str, Any]:
    """Return one bounded projection; SQL query output is the sole source of rows."""
    result = query_lineage(connection, identity, query.lineage)
    if result.get("status") != "available":
        return {**result, "projection": query.view}
    nodes = sorted(result.get("nodes", []), key=lambda row: row["name"])
    routes = sorted(result.get("routes", []), key=lambda row: (row["root"], row["nodes"]))
    edge_rows = _route_edges(routes)
    if len(nodes) > query.max_algorithm_nodes or len(edge_rows) > query.max_algorithm_nodes * 4:
        raise TheoremLineageProjectionError("bounded SQL result exceeds projection algorithm cap")
    payload = _base_payload(result, query, nodes, routes, edge_rows)
    if query.view == "tree":
        roots = sorted({route["root"] for route in routes})
        payload["tree"] = unfold_tree(
            roots,
            edge_rows,
            max_depth=query.max_tree_depth,
            max_nodes=query.lineage.max_nodes,
            max_bytes=query.max_tree_bytes,
            cap=query.max_algorithm_nodes,
        )
    elif query.view == "bottlenecks":
        payload["bottlenecks"] = _project_bottlenecks(nodes, routes, edge_rows, query)
    return payload


def _project_bottlenecks(
    nodes: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    edge_rows: list[tuple[str, str]],
    query: ProjectionQuery,
) -> dict[str, Any]:
    roots = sorted({route["root"] for route in routes})
    node_names = {row["name"] for row in nodes}
    if not roots or query.lineage.theorem not in node_names:
        raise TheoremLineageProjectionError(
            "bottlenecks requires at least one root-to-target route in the "
            "bounded result; run --view summary first, select an exact --root, "
            "or increase --max-nodes/--max-routes"
        )
    try:
        result = compute_dominators(
            [row["name"] for row in nodes],
            edge_rows,
            roots,
            query.lineage.theorem,
            cap=query.max_algorithm_nodes,
        )
        dominators = result.pop("dominators")
        assert isinstance(dominators, dict)
        summary = sorted(
            (
                {"node": node, "dominatorCount": len(values)}
                for node, values in dominators.items()
            ),
            key=lambda row: (-row["dominatorCount"], row["node"]),
        )
        result["dominatorSummary"] = summary[: query.max_dominator_rows]
        result["dominatorPopulation"] = len(summary)
        result["dominatorReturned"] = min(len(summary), query.max_dominator_rows)
        result["dominatorSummaryTruncated"] = len(summary) > query.max_dominator_rows
        return result
    except AlgorithmInputError as exc:
        raise TheoremLineageProjectionError(str(exc)) from exc


def _route_edges(routes: list[dict[str, Any]]) -> list[tuple[str, str]]:
    return sorted(
        {
            (source, target)
            for route in routes
            for source, target in zip(route["nodes"], route["nodes"][1:])
        }
    )


def _base_payload(
    result: dict[str, Any],
    query: ProjectionQuery,
    nodes: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    edges: list[tuple[str, str]],
) -> dict[str, Any]:
    return {
        **result,
        "projection": query.view,
        "nodes": nodes,
        "edges": [{"source": source, "target": target} for source, target in edges],
        "routes": routes,
        "collapses": _collapses(nodes),
        "branchPoints": _branch_points(edges),
        "projectionFingerprint": _fingerprint(query, nodes, edges),
        "nonclaim": result["nonclaim"],
    }


def _collapses(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for node in nodes:
        owner = str(node.get("ownerModule") or "<external>")
        groups.setdefault(owner, []).append(str(node["name"]))
    return [
        {"ownerModule": owner, "memberCount": len(members), "members": sorted(members)}
        for owner, members in sorted(groups.items())
    ]


def _branch_points(edges: list[tuple[str, str]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for source, _ in edges:
        counts[source] = counts.get(source, 0) + 1
    return [
        {"node": node, "outDegree": count} for node, count in sorted(counts.items()) if count > 1
    ]


def _fingerprint(
    query: ProjectionQuery, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]
) -> str:
    encoded = json.dumps(
        {
            "query": query.lineage.__dict__,
            "view": query.view,
            "nodes": [row["name"] for row in nodes],
            "edges": edges,
        },
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


__all__ = ["ProjectionQuery", "TheoremLineageProjectionError", "project_lineage"]
