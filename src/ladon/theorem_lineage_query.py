"""Bounded, SQL-first queries over stored theorem-lineage closures."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from ladon.theorem_lineage_store import LineageIdentity, inspect_lineage_closure


class TheoremLineageQueryError(ValueError):
    """A lineage query is invalid or cannot be answered from stored evidence."""


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
    recursive_row_limit: int = 10000
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
            ("recursive_row_limit", self.recursive_row_limit),
        ):
            if value < 1:
                raise TheoremLineageQueryError(f"{name} must be positive")


def query_lineage(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    query: LineageQuery,
) -> dict[str, Any]:
    """Run one bounded query against one fresh exact closure."""

    started = time.monotonic()
    status = inspect_lineage_closure(connection, query.theorem, identity)
    if status["status"] != "fresh":
        return {
            "schema": "ladon-theorem-lineage-result-v1",
            "operation": "lineage",
            "status": "unavailable",
            "reason": status.get("reason", status["status"]),
            "theorem": query.theorem,
            "authority": "unavailable",
            "query": _query_payload(query),
            "elapsedSeconds": round(time.monotonic() - started, 6),
            "nonclaim": _NONCLAIM,
        }
    closure_id = str(status["closureId"])
    walk_rows = _walk_rows(connection, closure_id, query)
    routes, route_truncated = _route_rows(connection, closure_id, query)
    edge_count = sum(len(route["edges"]) for route in routes)
    edge_truncated = edge_count > query.max_edges
    if edge_truncated:
        routes = _trim_routes_to_edge_cap(routes, query.max_edges)
    nodes = _node_rows(connection, closure_id, walk_rows)
    query_plan = _query_plan(connection, closure_id, query) if query.explain else []
    truncated = route_truncated or edge_truncated or len(walk_rows) > query.max_nodes
    return {
        "schema": "ladon-theorem-lineage-result-v1",
        "operation": "lineage",
        "status": "available",
        "theorem": query.theorem,
        "closureId": closure_id,
        "authority": "lean_environment",
        "freshness": "fresh",
        "query": _query_payload(query),
        "bounds": {
            "maxDepth": query.max_depth,
            "maxNodes": query.max_nodes,
            "maxEdges": query.max_edges,
            "maxRoutes": query.max_routes,
            "recursiveRowLimit": query.recursive_row_limit,
        },
        "nodes": nodes[: query.max_nodes],
        "routes": routes[: query.max_routes],
        "returned": {"nodes": min(len(nodes), query.max_nodes), "routes": min(len(routes), query.max_routes), "edges": min(edge_count, query.max_edges)},
        "truncated": truncated,
        "omissions": _omissions(query, walk_rows, routes, truncated),
        "queryPlan": query_plan,
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _NONCLAIM,
    }


def _walk_rows(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
) -> list[dict[str, Any]]:
    join = "e.source = walk.node" if query.direction == "ancestry" else "e.target = walk.node"
    next_node = "e.target" if query.direction == "ancestry" else "e.source"
    edge_filter, edge_values = _edge_filter("e.kind", query.edge_kind)
    sql = f"""
        WITH RECURSIVE walk(node, depth, path, edge_kinds) AS (
            SELECT ?, 0, '|' || ? || '|', ''
            UNION ALL
            SELECT {next_node}, walk.depth + 1,
                   walk.path || {next_node} || '|',
                   CASE WHEN walk.edge_kinds = '' THEN e.kind
                        ELSE walk.edge_kinds || ',' || e.kind END
            FROM walk
            JOIN lineage_edges e ON e.closure_id = ? AND {join}
            WHERE walk.depth < ?
              AND instr(walk.path, '|' || {next_node} || '|') = 0
              AND ({edge_filter})
            LIMIT ?
        )
        SELECT walk.node, walk.depth, walk.path, walk.edge_kinds
        FROM walk
        JOIN lineage_nodes n ON n.closure_id = ? AND n.name = walk.node
        WHERE { _node_filter("n", query) }
        ORDER BY walk.depth, walk.node
        LIMIT ?
    """
    values = [query.theorem, query.theorem, closure_id, query.max_depth]
    values.extend(edge_values)
    values.extend((query.recursive_row_limit, closure_id, query.max_nodes + 1))
    return [dict(row) for row in connection.execute(sql, values)]


def _route_rows(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
) -> tuple[list[dict[str, Any]], bool]:
    rows = _walk_rows(connection, closure_id, query)
    routes = []
    for row in rows:
        if row["node"] == query.theorem or not _is_boundary_node(connection, closure_id, row["node"], query):
            continue
        nodes = str(row["path"]).strip("|").split("|")
        edges = str(row["edge_kinds"]).split(",") if row["edge_kinds"] else []
        if query.direction == "ancestry":
            nodes.reverse()
            edges.reverse()
        routes.append(
            {
                "root": nodes[0],
                "target": nodes[-1],
                "depth": len(edges),
                "nodes": nodes,
                "edges": edges,
            }
        )
    routes.sort(key=lambda item: (item["root"], item["depth"], item["edges"], item["nodes"]))
    return routes[: query.max_routes + 1], len(routes) > query.max_routes


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
    placeholders = ",".join("?" for _ in names)
    rows = connection.execute(
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
        [closure_id, *names],
    ).fetchall()
    result = [dict(row) for row in rows]
    components = {
        str(row["member"]): str(row["component_id"])
        for row in connection.execute(
            f"SELECT member, component_id FROM lineage_scc_members WHERE closure_id = ? AND member IN ({placeholders})",
            [closure_id, *names],
        )
    }
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
        if not kept and size > max_edges:
            return [route]
        kept.append(route)
        used += size
    return kept


_NONCLAIM = (
    "Lineage routes are dependencies of one compiled theorem value and its type; "
    "they are not all possible alternative proofs or a unique proof tree."
)


__all__ = ["LineageQuery", "TheoremLineageQueryError", "query_lineage"]
