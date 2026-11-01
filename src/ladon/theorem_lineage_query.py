"""Bounded, SQL-first queries over stored theorem-lineage closures."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from ladon.evidence_receipt_readers import stored_query_receipt
from ladon.theorem_lineage_store import LineageIdentity, inspect_lineage_closure


class TheoremLineageQueryError(ValueError):
    """A lineage query is invalid or cannot be answered from stored evidence."""


@dataclass
class _WalkState:
    visited: dict[str, dict[str, Any]]
    effective_edge_cap: int
    distinct_nodes_expanded: int = 0
    adjacency_rows_examined: int = 0
    node_limit_reached: bool = False
    work_limit_reached: bool = False
    depth_limited: bool = False


@dataclass(frozen=True)
class LineageQuery:
    """Finite SQL query parameters for one theorem closure."""

    theorem: str
    boundary: str = "trust"
    roots: tuple[str, ...] = ()
    edge_kind: str = "all"
    direction: str = "ancestry"
    include_generated: bool = True
    max_depth: int = 32
    max_nodes: int = 1000
    max_edges: int = 4000
    max_routes: int = 20
    max_traversal_edges: int = 100000
    explain: bool = False

    def __post_init__(self) -> None:
        if not self.theorem:
            raise TheoremLineageQueryError("theorem name is required")
        if self.boundary not in {"trust", "project", "external", "package", "declaration"}:
            raise TheoremLineageQueryError("unsupported root boundary")
        if self.edge_kind not in {"all", "type", "value"}:
            raise TheoremLineageQueryError("unsupported edge kind")
        if self.direction not in {"ancestry", "dependencies"}:
            raise TheoremLineageQueryError("unsupported lineage direction")
        if self.boundary in {"package", "declaration"} and not self.roots:
            raise TheoremLineageQueryError("selected root boundary requires --root")
        for name, value in (
            ("max_depth", self.max_depth),
            ("max_nodes", self.max_nodes),
            ("max_edges", self.max_edges),
            ("max_routes", self.max_routes),
            ("max_traversal_edges", self.max_traversal_edges),
        ):
            if value < 1:
                raise TheoremLineageQueryError(f"{name} must be positive")


def query_lineage(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    query: LineageQuery,
) -> dict[str, Any]:
    """Run one bounded query in a coherent read snapshot."""

    owns_snapshot = not connection.in_transaction
    if owns_snapshot:
        connection.execute("BEGIN")
    try:
        return _query_lineage_snapshot(connection, identity, query)
    finally:
        if owns_snapshot and connection.in_transaction:
            connection.rollback()


def _query_lineage_snapshot(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    query: LineageQuery,
) -> dict[str, Any]:
    """Run a bounded query after its caller established a coherent snapshot."""

    started = time.monotonic()
    status = inspect_lineage_closure(connection, query.theorem, identity)
    if status["status"] != "fresh":
        return {
            "schema": "ladon-theorem-lineage-result-v2",
            "operation": "lineage",
            "status": "unavailable",
            "reason": status.get("reason", status["status"]),
            "theorem": query.theorem,
            "authority": "unavailable",
            "evidenceReceipt": lineage_query_receipt(status, query.theorem),
            "query": _query_payload(query),
            "elapsedSeconds": round(time.monotonic() - started, 6),
            "nonclaim": _NONCLAIM,
        }
    closure_id = str(status["closureId"])
    walk = _discover_nodes(connection, closure_id, query)
    walk_rows = walk["rows"]
    route_candidates, route_truncated = _route_rows_from_walk(
        connection, closure_id, query, walk_rows
    )
    routes = route_candidates[: query.max_routes]
    edge_count = sum(len(route["edges"]) for route in routes)
    edge_truncated = edge_count > query.max_edges
    if edge_truncated:
        routes = _trim_routes_to_edge_cap(routes, query.max_edges)
    nodes = _node_rows(connection, closure_id, walk_rows)
    query_plan = _query_plan(connection, closure_id, query) if query.explain else []
    node_limit_reached = bool(walk["node_limit_reached"])
    truncated = (
        route_truncated or edge_truncated or node_limit_reached
        or walk["work_limit_reached"] or walk["depth_limited"]
    )
    boundary_count = _boundary_population_count(connection, closure_id, query)
    returned_routes = routes[: query.max_routes]
    route_occurrences, route_pairs, route_typed_edges = _route_edge_counts(returned_routes)
    return {
        "schema": "ladon-theorem-lineage-result-v2",
        "operation": "lineage",
        "status": "available",
        "theorem": query.theorem,
        "closureId": closure_id,
        "authority": "lean_environment",
        "freshness": "fresh",
        "evidenceReceipt": lineage_query_receipt(status, query.theorem),
        "query": _query_payload(query),
        "bounds": {
            "maxDepth": query.max_depth,
            "maxNodes": query.max_nodes,
            "maxEdges": query.max_edges,
            "maxRoutes": query.max_routes,
            "maxTraversalEdges": query.max_traversal_edges,
        },
        "acquisition": {
            "rowsObserved": len(walk_rows),
            "distinctNodesExpanded": walk["distinct_nodes_expanded"],
            "typedAdjacencyRowsExamined": walk["adjacency_rows_examined"],
            "traversalWorkLimitReached": walk["work_limit_reached"],
            "nodeLimitReached": node_limit_reached,
            "depthLimitReached": walk["depth_limited"],
            "boundaryPopulation": boundary_count,
        },
        "truncation": {
            "nodeLimited": node_limit_reached,
            "depthLimited": walk["depth_limited"],
            "traversalWorkLimited": walk["work_limit_reached"],
            "routeLimited": route_truncated,
            "edgeLimited": edge_truncated,
        },
        "nodes": nodes[: query.max_nodes],
        "routes": returned_routes,
        "returned": {
            "nodes": min(len(nodes), query.max_nodes),
            "routes": len(returned_routes),
            "routeEdgeOccurrences": route_occurrences,
            "uniqueRouteEdgePairs": route_pairs,
            "uniqueTypedRouteEdges": route_typed_edges,
        },
        "truncated": truncated,
        "routeExplanation": _route_explanation(
            query, routes, truncated, boundary_count
        ),
        "omissions": _omissions(query, walk_rows, routes, truncated),
        "queryPlan": query_plan,
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _NONCLAIM,
    }


def _boundary_population_count(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
) -> int:
    """Count classified boundary nodes for an explicit route explanation."""

    if query.boundary == "trust":
        row = connection.execute(
            "SELECT count(DISTINCT target) FROM lineage_trust WHERE closure_id = ?",
            (closure_id,),
        ).fetchone()
        return int(row[0] or 0)
    if query.boundary == "declaration":
        return len(query.roots)
    row = connection.execute(
        "SELECT count(*) FROM lineage_nodes WHERE closure_id = ? AND "
        "(project_owned = 1 OR external_frontier = 1)",
        (closure_id,),
    ).fetchone()
    return int(row[0] or 0)


def _route_explanation(
    query: LineageQuery,
    routes: list[dict[str, Any]],
    truncated: bool,
    boundary_count: int,
) -> dict[str, Any]:
    """Explain empty route populations without upgrading them to absence claims."""

    if routes:
        return {"status": "routes-present", "message": "bounded routes returned"}
    if truncated:
        return {
            "status": "unknown-bounded",
            "message": "no routes returned within the selected bounds",
        }
    if boundary_count == 0:
        return {
            "status": "no-classified-boundary",
            "message": (
                f"no {query.boundary} boundary nodes were classified in the stored closure"
            ),
        }
    return {
        "status": "no-route-within-boundary",
        "message": (
            f"{boundary_count} {query.boundary} boundary nodes were classified, "
            "but none has a route to the target under this query"
        ),
    }


def _walk_rows(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
) -> list[dict[str, Any]]:
    return _discover_nodes(connection, closure_id, query)["rows"]


def _discover_nodes(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> dict[str, Any]:
    """Discover each declaration once before constructing bounded routes."""

    state = _WalkState(
        visited={query.theorem: {"depth": 0, "parent": None, "kind": None}},
        effective_edge_cap=query.max_traversal_edges,
    )
    frontier = [query.theorem]
    while frontier and not state.work_limit_reached and not state.node_limit_reached:
        next_frontier: set[str] = set()
        for node_batch in _chunks(sorted(frontier), 250):
            state.distinct_nodes_expanded += len(node_batch)
            next_frontier.update(
                _expand_frontier_batch(connection, closure_id, node_batch, query, state)
            )
            if state.work_limit_reached or state.node_limit_reached:
                break
        frontier = sorted(next_frontier)

    walk_rows = _materialize_walk_rows(state.visited)
    return {
        "rows": walk_rows,
        "distinct_nodes_expanded": state.distinct_nodes_expanded,
        "adjacency_rows_examined": state.adjacency_rows_examined,
        "work_limit_reached": state.work_limit_reached,
        "node_limit_reached": state.node_limit_reached,
        "depth_limited": state.depth_limited,
    }


def _expand_frontier_batch(
    connection: sqlite3.Connection,
    closure_id: str,
    node_batch: list[str],
    query: LineageQuery,
    state: _WalkState,
) -> set[str]:
    batch_depth = min(int(state.visited[node]["depth"]) for node in node_batch)
    rows = _adjacency_rows(
        connection, closure_id, node_batch, query,
        limit=state.effective_edge_cap - state.adjacency_rows_examined + 1,
    )
    next_frontier = set()
    for row in rows:
        if state.adjacency_rows_examined >= state.effective_edge_cap:
            state.work_limit_reached = True
            break
        state.adjacency_rows_examined += 1
        candidate = str(row["nextNode"])
        if candidate in state.visited or (not query.include_generated and row["generated"]):
            continue
        if batch_depth >= query.max_depth:
            state.depth_limited = True
            continue
        if len(state.visited) >= query.max_nodes:
            state.node_limit_reached = True
            break
        state.visited[candidate] = {
            "depth": batch_depth + 1,
            "parent": str(row["currentNode"]),
            "kind": str(row["kind"]),
        }
        next_frontier.add(candidate)
    return next_frontier


def _adjacency_rows(
    connection: sqlite3.Connection,
    closure_id: str,
    current_nodes: list[str],
    query: LineageQuery,
    *,
    limit: int,
) -> list[sqlite3.Row]:
    if not current_nodes or limit <= 0:
        return []
    join_key = "e.source" if query.direction == "ancestry" else "e.target"
    next_key = "e.target" if query.direction == "ancestry" else "e.source"
    filter_sql, filter_values = _edge_filter("e.kind", query.edge_kind)
    placeholders = ",".join("?" for _ in current_nodes)
    return connection.execute(
        f"""SELECT {join_key} AS currentNode, {next_key} AS nextNode,
                   e.kind, n.compiler_generated AS generated
            FROM lineage_edges e
            JOIN lineage_nodes n ON n.closure_id=e.closure_id AND n.name={next_key}
            WHERE e.closure_id=? AND {join_key} IN ({placeholders})
              AND ({filter_sql})
            ORDER BY currentNode, e.kind, nextNode
            LIMIT ?""",
        (closure_id, *current_nodes, *filter_values, limit),
    ).fetchall()


def _materialize_walk_rows(
    visited: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "node": node,
            "depth": int(item["depth"]),
            "parent": item["parent"],
            "edge_kind": item["kind"],
        }
        for node, item in sorted(visited.items(), key=lambda pair: (pair[1]["depth"], pair[0]))
    ]


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[offset : offset + size] for offset in range(0, len(items), size)]


def _route_rows(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
) -> tuple[list[dict[str, Any]], bool]:
    rows = _walk_rows(connection, closure_id, query)
    return _route_rows_from_walk(connection, closure_id, query, rows)


def _route_rows_from_walk(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    parent_rows = {str(row["node"]): row for row in rows}
    boundary_nodes = sorted(_boundary_nodes(
        connection, closure_id, query,
        set(parent_rows) - {query.theorem},
    ))
    routes = [
        _representative_route(node, parent_rows, query)
        for node in boundary_nodes[: query.max_routes + 1]
    ]
    routes.sort(key=lambda item: (item["root"], item["depth"], item["edges"], item["nodes"]))
    return routes, len(boundary_nodes) > query.max_routes


def _route_edge_counts(routes: list[dict[str, Any]]) -> tuple[int, int, int]:
    pairs = set()
    typed = set()
    occurrences = 0
    for route in routes:
        for source, target, kind in zip(
            route["nodes"], route["nodes"][1:], route["edges"]
        ):
            occurrences += 1
            pairs.add((source, target))
            typed.add((source, target, kind))
    return occurrences, len(pairs), len(typed)


def _representative_route(
    boundary: str, parents: dict[str, dict[str, Any]], query: LineageQuery
) -> dict[str, Any]:
    reverse_nodes = [boundary]
    reverse_edges = []
    cursor = boundary
    while parents[cursor]["parent"] is not None:
        reverse_edges.append(str(parents[cursor]["edge_kind"]))
        cursor = str(parents[cursor]["parent"])
        reverse_nodes.append(cursor)
    nodes = list(reversed(reverse_nodes))
    edges = list(reversed(reverse_edges))
    if query.direction == "ancestry":
        nodes.reverse()
        edges.reverse()
    return {
        "root": nodes[0],
        "target": nodes[-1],
        "depth": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def _boundary_nodes(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
    names: set[str],
) -> set[str]:
    if not names:
        return set()
    if query.boundary == "declaration":
        return names & set(query.roots)
    if query.boundary == "trust":
        return _trust_boundary_nodes(connection, closure_id, names)
    rows = _lineage_boundary_rows(connection, closure_id, names)
    return _filter_boundary_rows(rows, query)


def _filter_boundary_rows(rows: list[sqlite3.Row], query: LineageQuery) -> set[str]:
    if query.boundary == "project":
        return {str(row[0]) for row in rows if row[1]}
    if query.boundary == "external":
        return {str(row[0]) for row in rows if row[2]}
    return _package_boundary_nodes(rows, query.roots)


def _package_boundary_nodes(rows: list[sqlite3.Row], roots: tuple[str, ...]) -> set[str]:
    return {str(row[0]) for row in rows if any(str(row[3]) == root or str(row[3]).startswith(f"{root}.") for root in roots)}


def _trust_boundary_nodes(connection: sqlite3.Connection, closure_id: str, names: set[str]) -> set[str]:
    result = set()
    for batch in _chunks(sorted(names), 250):
        placeholders = ",".join("?" for _ in batch)
        rows = connection.execute(
            f"SELECT target FROM lineage_trust WHERE closure_id = ? AND target IN ({placeholders})",
            (closure_id, *batch),
        ).fetchall()
        result.update(str(row[0]) for row in rows)
    return result


def _lineage_boundary_rows(connection: sqlite3.Connection, closure_id: str, names: set[str]) -> list[sqlite3.Row]:
    rows = []
    for batch in _chunks(sorted(names), 250):
        placeholders = ",".join("?" for _ in batch)
        rows.extend(connection.execute(
            f"SELECT name,project_owned,external_frontier,owner_module FROM lineage_nodes WHERE closure_id = ? AND name IN ({placeholders})",
            (closure_id, *batch),
        ).fetchall())
    return rows


def _is_boundary_node(
    connection: sqlite3.Connection,
    closure_id: str,
    node: str,
    query: LineageQuery,
) -> bool:
    if query.boundary == "trust":
        return bool(connection.execute(
            "SELECT 1 FROM lineage_trust WHERE closure_id = ? AND target = ? LIMIT 1",
            (closure_id, node),
        ).fetchone())
    if query.boundary == "declaration":
        return node in query.roots
    row = connection.execute(
        "SELECT project_owned, external_frontier, owner_module FROM lineage_nodes WHERE closure_id = ? AND name = ?",
        (closure_id, node),
    ).fetchone()
    if row is None:
        return False
    if query.boundary == "project":
        return bool(row[0]) and node != query.theorem
    if query.boundary == "external":
        return bool(row[1])
    return any(str(row[2]) == root or str(row[2]).startswith(f"{root}.") for root in query.roots)


def _node_rows(
    connection: sqlite3.Connection,
    closure_id: str,
    walk_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    names = sorted({str(row["node"]) for row in walk_rows})
    if not names:
        return []
    result = []
    for name_batch in _chunks(names, 250):
        placeholders = ",".join("?" for _ in name_batch)
        result.extend(connection.execute(
            f"""
        SELECT n.name, n.owner_module AS ownerModule, n.kind,
               n.project_owned AS projectOwned,
               n.external_frontier AS externalFrontier,
               COALESCE(n.source_path, (
                   SELECT d.path FROM declarations d
                   WHERE d.candidate_name = n.name AND d.module = n.owner_module
                   ORDER BY d.id LIMIT 1
               )) AS sourcePath,
               COALESCE(n.source_line, (
                   SELECT d.line FROM declarations d
                   WHERE d.candidate_name = n.name AND d.module = n.owner_module
                   ORDER BY d.id LIMIT 1
               )) AS sourceLine,
               COALESCE(n.source_column, (
                   SELECT d.column_number FROM declarations d
                   WHERE d.candidate_name = n.name AND d.module = n.owner_module
                   ORDER BY d.id LIMIT 1
               )) AS sourceColumn,
               CASE
                   WHEN n.source_path IS NOT NULL THEN n.source_status
                   WHEN n.project_owned = 1 AND EXISTS (
                       SELECT 1 FROM declarations d
                       WHERE d.candidate_name = n.name AND d.module = n.owner_module
                   ) THEN 'indexed_lexical_source'
                   ELSE n.source_status
               END AS sourceStatus
        FROM lineage_nodes n
        WHERE n.closure_id = ? AND n.name IN ({placeholders})
        ORDER BY n.name
        """,
        [closure_id, *name_batch],
        ).fetchall())
    result = [dict(row) for row in result]
    from ladon.idea_history import attach_lineage_history

    attach_lineage_history(connection, result)
    components = {}
    for name_batch in _chunks(names, 250):
        placeholders = ",".join("?" for _ in name_batch)
        components.update({
            str(row["member"]): str(row["component_id"])
            for row in connection.execute(
                f"SELECT member, component_id FROM lineage_scc_members WHERE closure_id = ? AND member IN ({placeholders})",
                [closure_id, *name_batch],
            )
        })
    for row in result:
        row["sccId"] = components.get(str(row["name"]))
    return result


def _query_plan(connection: sqlite3.Connection, closure_id: str, query: LineageQuery) -> list[str]:
    forward = connection.execute(
        "EXPLAIN QUERY PLAN SELECT target FROM lineage_edges WHERE closure_id = ? AND source = ?",
        (closure_id, query.theorem),
    ).fetchall()
    reverse = connection.execute(
        "EXPLAIN QUERY PLAN SELECT source FROM lineage_edges WHERE closure_id = ? AND target = ?",
        (closure_id, query.theorem),
    ).fetchall()
    return [str(tuple(row)) for row in [*forward, *reverse]]


def _edge_filter(column: str, edge_kind: str) -> tuple[str, list[str]]:
    if edge_kind == "all":
        return "1 = 1", []
    return f"{column} = ?", [edge_kind]


def _node_filter(alias: str, query: LineageQuery) -> str:
    if query.include_generated:
        return "1 = 1"
    return f"{alias}.compiler_generated = 0"


def _query_payload(query: LineageQuery) -> dict[str, Any]:
    return {
        "theorem": query.theorem,
        "boundary": query.boundary,
        "roots": list(query.roots),
        "edgeKind": query.edge_kind,
        "direction": query.direction,
        "includeGenerated": query.include_generated,
    }


def _omissions(
    query: LineageQuery,
    walk_rows: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    truncated: bool,
) -> list[dict[str, str]]:
    if not truncated:
        return []
    return [{"kind": "bound", "subject": query.theorem, "reason": "lineage_query_cap"}]


def _trim_routes_to_edge_cap(routes: list[dict[str, Any]], max_edges: int) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    used = 0
    for route in routes:
        size = len(route["edges"])
        if kept and used + size > max_edges:
            break
        if used + size > max_edges:
            break
        kept.append(route)
        used += size
    return kept


_NONCLAIM = (
    "Lineage routes are dependencies of one compiled theorem value and its type; "
    "they are not all possible alternative proofs or a unique proof tree."
)


__all__ = ["LineageQuery", "TheoremLineageQueryError", "query_lineage"]


def lineage_query_receipt(status: dict[str, Any], theorem: str, *, projection_kind: str = "sqlite-row") -> dict[str, Any]:
    """Keep dependency acquisition distinct from an attributable theorem check."""

    closure_id = status.get("closureId")
    freshness = {"fresh": "fresh", "stale-source": "stale"}.get(status["status"], "not-assessed")
    return stored_query_receipt(
        "theorem-lineage", theorem, observed=closure_id is not None,
        source_ref="lineage:" + closure_id if closure_id is not None else None,
        source_freshness=freshness, projection_kind=projection_kind,
    )
