"""Complete, bounded projections of one stored theorem-lineage closure."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from typing import Any

from ladon.theorem_lineage_query import (
    LineageQuery,
    _node_rows,
    lineage_query_receipt,
)
from ladon.theorem_lineage_store import LineageIdentity, inspect_lineage_closure


def query_stored_closure(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    query: LineageQuery,
) -> dict[str, Any]:
    """Read one identity-checked closure as an induced, typed, endpoint-closed graph."""

    owns_snapshot = not connection.in_transaction
    if owns_snapshot:
        connection.execute("BEGIN")
    try:
        return _query_stored_closure_snapshot(connection, identity, query)
    finally:
        if owns_snapshot and connection.in_transaction:
            connection.rollback()


def _query_stored_closure_snapshot(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    query: LineageQuery,
) -> dict[str, Any]:
    started = time.monotonic()
    status = inspect_lineage_closure(connection, query.theorem, identity)
    if status["status"] != "fresh":
        return {
            "schema": "ladon-theorem-lineage-result-v2",
            "operation": "lineage",
            "projection": "closure",
            "status": "unavailable",
            "reason": status.get("reason", status["status"]),
            "theorem": query.theorem,
            "authority": "unavailable",
            "evidenceReceipt": lineage_query_receipt(
                status, query.theorem, projection_kind="sqlite-row"
            ),
            "elapsedSeconds": round(time.monotonic() - started, 6),
            "nonclaim": _NONCLAIM,
        }

    closure_id = str(status["closureId"])
    closure = connection.execute(
        "SELECT semantic_status,authority,node_count,edge_count FROM lineage_closures "
        "WHERE closure_id=? AND theorem_name=? AND active=1",
        (closure_id, query.theorem),
    ).fetchone()
    if closure is None:
        return _unavailable(query, status, started, "closure_changed")

    return _available_closure_result(
        connection, query, status, closure_id, closure, started
    )


def _available_closure_result(
    connection: sqlite3.Connection,
    query: LineageQuery,
    status: dict[str, Any],
    closure_id: str,
    closure: sqlite3.Row,
    started: float,
) -> dict[str, Any]:
    source_coverage = _source_coverage(connection, closure_id, closure)
    nodes, edges, graph_coverage = _selected_graph(
        connection, closure_id, query
    )
    external_coverage = _external_coverage(connection, closure_id, query, nodes)
    coverage = {
        "version": 1,
        "sourceClosure": source_coverage,
        "selectedGraph": graph_coverage,
        "representativeRoutes": {
            "status": "not-requested",
            "notApplicableOptions": [
                "boundary", "roots", "direction", "maxDepth", "maxRoutes",
                "maxTraversalEdges",
            ],
        },
        "externalExpansion": external_coverage,
    }
    fingerprint = _fingerprint(query, nodes, edges, coverage)
    returned = {
        "nodes": len(nodes), "edges": len(edges),
        "typedEdges": len(edges), "routes": 0,
    }
    return {
        "schema": "ladon-theorem-lineage-result-v2",
        "operation": "lineage",
        "projection": "closure",
        "status": "available",
        "theorem": query.theorem,
        "closureId": closure_id,
        "authority": str(closure[1]),
        "freshness": "fresh",
        "evidenceReceipt": lineage_query_receipt(
            status, query.theorem, projection_kind="sqlite-row"
        ),
        "query": {
            "selection": "whole-stored-closure",
            "edgeKind": query.edge_kind,
            "includeGenerated": query.include_generated,
        },
        "bounds": {"maxNodes": query.max_nodes, "maxEdges": query.max_edges},
        "coverage": coverage,
        "nodes": nodes,
        "edges": edges,
        "routes": [],
        "returned": returned,
        "truncated": graph_coverage["status"] != "complete",
        "omissions": _omission_rows(graph_coverage["omissions"]),
        "projectionFingerprint": fingerprint,
        "nonclaim": _NONCLAIM,
        "elapsedSeconds": round(time.monotonic() - started, 6),
    }


def _source_coverage(
    connection: sqlite3.Connection, closure_id: str, closure: sqlite3.Row
) -> dict[str, Any]:
    stored_nodes = _row_count(connection, "lineage_nodes", closure_id)
    stored_edges = _row_count(connection, "lineage_edges", closure_id)
    omissions = _row_count(connection, "lineage_omissions", closure_id)
    recorded_match = int(closure[2]) == stored_nodes and int(closure[3]) == stored_edges
    complete = str(closure[0]) == "complete" and recorded_match and omissions == 0
    return {
        "status": "complete" if complete else "partial-or-unknown",
        "recordedSemanticStatus": str(closure[0]),
        "authority": str(closure[1]),
        "closureId": closure_id,
        "storedNodes": stored_nodes,
        "storedTypedEdges": stored_edges,
        "projectOwnedNodes": _node_class_count(connection, closure_id, "project_owned"),
        "externalFrontierNodes": _node_class_count(connection, closure_id, "external_frontier"),
        "recordedNodes": int(closure[2]),
        "recordedTypedEdges": int(closure[3]),
        "storedOmissionRecords": omissions,
        "recordedCountsMatch": recorded_match,
    }


def _selected_graph(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected_count = _count_selected_nodes(connection, closure_id, query)
    selected_names = _selected_names(connection, closure_id, query)
    rows = _node_rows(connection, closure_id, [{"node": name} for name in selected_names])
    by_name = {str(row["name"]): row for row in rows}
    nodes = [by_name[name] for name in selected_names if name in by_name]
    selected_edges = _count_selected_edges(connection, closure_id, query)
    edges = _selected_edges(connection, closure_id, query)[: query.max_edges]
    omissions = {
        "generatedNodes": _count_generated_omissions(connection, closure_id, query),
        "nodesByLimit": max(0, selected_count - len(nodes)),
        "edgesByNodeOrEdgeLimit": max(0, selected_edges - len(edges)),
        "filteredTypedEdges": _count_filtered_edges(connection, closure_id, query),
    }
    complete = omissions["nodesByLimit"] == 0 and omissions["edgesByNodeOrEdgeLimit"] == 0
    return nodes, edges, {
        "selection": "whole-stored-closure",
        "edgeKind": query.edge_kind,
        "includeGenerated": query.include_generated,
        "status": "complete" if complete else "partial",
        "selectedUniqueNodes": selected_count,
        "selectedTypedEdges": selected_edges,
        "returnedUniqueNodes": len(nodes),
        "returnedTypedEdges": len(edges),
        "omissions": omissions,
        "limits": {"maxNodes": query.max_nodes, "maxEdges": query.max_edges},
    }


def _external_coverage(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
    nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "scope": "project-owned-with-library-frontier",
        "selectedFrontierNodes": _count_external_nodes(connection, closure_id, query),
        "returnedFrontierNodes": sum(bool(row["externalFrontier"]) for row in nodes),
        "selectedIncidentTypedEdges": _count_external_edges(connection, closure_id, query),
        "libraryTransitiveExpansion": "not-performed",
    }


def _row_count(connection: sqlite3.Connection, table: str, closure_id: str) -> int:
    return int(connection.execute(
        f"SELECT count(*) FROM {table} WHERE closure_id=?", (closure_id,)
    ).fetchone()[0])


def _node_class_count(
    connection: sqlite3.Connection, closure_id: str, field: str
) -> int:
    if field not in {"project_owned", "external_frontier"}:
        raise ValueError("unsupported stored lineage node class")
    return int(connection.execute(
        f"SELECT count(*) FROM lineage_nodes WHERE closure_id=? AND {field}=1",
        (closure_id,),
    ).fetchone()[0])


def _selected_names(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> list[str]:
    generated_filter = "" if query.include_generated else "AND (compiler_generated=0 OR name=?)"
    params = (closure_id, query.theorem, query.theorem, query.max_nodes) if not query.include_generated else (
        closure_id, query.theorem, query.max_nodes
    )
    return [str(row[0]) for row in connection.execute(
        f"SELECT name FROM lineage_nodes WHERE closure_id=? {generated_filter} "
        "ORDER BY CASE WHEN name=? THEN 0 ELSE 1 END,name LIMIT ?",
        params,
    ).fetchall()]


def _count_selected_nodes(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> int:
    generated_filter = "" if query.include_generated else "AND (compiler_generated=0 OR name=?)"
    params = (closure_id, query.theorem) if not query.include_generated else (closure_id,)
    return int(connection.execute(
        f"SELECT count(*) FROM lineage_nodes WHERE closure_id=? {generated_filter}",
        params,
    ).fetchone()[0])


def _count_selected_edges(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> int:
    source_filter = "" if query.include_generated else "AND (s.compiler_generated=0 OR s.name=?)"
    target_filter = "" if query.include_generated else "AND (t.compiler_generated=0 OR t.name=?)"
    kind_filter = "" if query.edge_kind == "all" else "AND e.kind=?"
    params: tuple[Any, ...] = (closure_id, closure_id)
    if not query.include_generated:
        params += (query.theorem, query.theorem)
    if query.edge_kind != "all":
        params += (query.edge_kind,)
    return int(connection.execute(
        f"""SELECT count(*) FROM lineage_edges e
            JOIN lineage_nodes s ON s.closure_id=e.closure_id AND s.name=e.source
            JOIN lineage_nodes t ON t.closure_id=e.closure_id AND t.name=e.target
            WHERE e.closure_id=? AND s.closure_id=?
              {source_filter}
              {target_filter}
              {kind_filter}""",
        params,
    ).fetchone()[0])


def _selected_edges(
    connection: sqlite3.Connection,
    closure_id: str,
    query: LineageQuery,
) -> list[dict[str, Any]]:
    generated_filter = "" if query.include_generated else "AND (compiler_generated=0 OR name=?)"
    selection = "(SELECT name FROM lineage_nodes n WHERE n.closure_id=? " + generated_filter + \
        " ORDER BY CASE WHEN name=? THEN 0 ELSE 1 END,name LIMIT ?)"
    kind_filter = "" if query.edge_kind == "all" else "AND e.kind=?"
    params: list[Any] = []
    for _ in range(2):
        params.append(closure_id)
        if not query.include_generated:
            params.append(query.theorem)
        params.extend((query.theorem, query.max_nodes))
    params.append(closure_id)
    if query.edge_kind != "all":
        params.append(query.edge_kind)
    params.append(query.max_edges + 1)
    rows = connection.execute(
        f"""SELECT e.source,e.target,e.kind,
                   e.target_owner_module AS targetOwnerModule,
                   e.target_kind AS targetKind FROM lineage_edges e
            JOIN {selection} s ON s.name=e.source
            JOIN {selection} t ON t.name=e.target
            WHERE e.closure_id=? {kind_filter}
            ORDER BY source,target,kind LIMIT ?""",
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _count_external_nodes(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> int:
    generated_filter = "" if query.include_generated else "AND (compiler_generated=0 OR name=?)"
    params = (closure_id, query.theorem) if not query.include_generated else (closure_id,)
    return int(connection.execute(
        f"SELECT count(*) FROM lineage_nodes WHERE closure_id=? AND external_frontier=1 {generated_filter}",
        params,
    ).fetchone()[0])


def _count_external_edges(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> int:
    source_filter = "" if query.include_generated else "AND (s.compiler_generated=0 OR s.name=?)"
    target_filter = "" if query.include_generated else "AND (t.compiler_generated=0 OR t.name=?)"
    kind_filter = "" if query.edge_kind == "all" else "AND e.kind=?"
    params: tuple[Any, ...] = (closure_id,)
    if not query.include_generated:
        params += (query.theorem, query.theorem)
    if query.edge_kind != "all":
        params += (query.edge_kind,)
    return int(connection.execute(
        f"""SELECT count(*) FROM lineage_edges e
            JOIN lineage_nodes s ON s.closure_id=e.closure_id AND s.name=e.source
            JOIN lineage_nodes t ON t.closure_id=e.closure_id AND t.name=e.target
            WHERE e.closure_id=? {source_filter} {target_filter}
              AND EXISTS (SELECT 1 FROM lineage_nodes n WHERE n.closure_id=e.closure_id
                AND n.external_frontier=1 AND n.name IN (e.source,e.target)
                {'' if query.include_generated else 'AND (n.compiler_generated=0 OR n.name=?)'})
              {kind_filter}""",
        (*params[:3], *(() if query.include_generated else (query.theorem,)), *params[3:]),
    ).fetchone()[0])


def _count_generated_omissions(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> int:
    if query.include_generated:
        return 0
    return int(connection.execute(
        "SELECT count(*) FROM lineage_nodes WHERE closure_id=? AND compiler_generated=1 AND name<>?",
        (closure_id, query.theorem),
    ).fetchone()[0])


def _count_filtered_edges(
    connection: sqlite3.Connection, closure_id: str, query: LineageQuery
) -> int:
    if query.edge_kind == "all":
        return 0
    source_filter = "" if query.include_generated else "AND (s.compiler_generated=0 OR s.name=?)"
    target_filter = "" if query.include_generated else "AND (t.compiler_generated=0 OR t.name=?)"
    params: tuple[Any, ...] = (closure_id, query.edge_kind)
    if not query.include_generated:
        params += (query.theorem, query.theorem)
    return int(connection.execute(
        f"""SELECT count(*) FROM lineage_edges e
            JOIN lineage_nodes s ON s.closure_id=e.closure_id AND s.name=e.source
            JOIN lineage_nodes t ON t.closure_id=e.closure_id AND t.name=e.target
            WHERE e.closure_id=? AND e.kind<>? {source_filter} {target_filter}""",
        params,
    ).fetchone()[0])


def _fingerprint(
    query: LineageQuery,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> str:
    payload = {
        "selection": "whole-stored-closure",
        "edgeKind": query.edge_kind,
        "includeGenerated": query.include_generated,
        "maxNodes": query.max_nodes,
        "maxEdges": query.max_edges,
        "nodes": [row["name"] for row in nodes],
        "edges": [(row["source"], row["target"], row["kind"]) for row in edges],
        "coverage": coverage,
    }
    return _canonical_fingerprint(payload)


def refresh_closure_fingerprint(result: dict[str, Any]) -> None:
    """Recompute a closure fingerprint after a trusted metadata projection."""

    query = result["query"]
    bounds = result["bounds"]
    result["projectionFingerprint"] = _canonical_fingerprint({
        "selection": query["selection"],
        "edgeKind": query["edgeKind"],
        "includeGenerated": query["includeGenerated"],
        "maxNodes": bounds["maxNodes"],
        "maxEdges": bounds["maxEdges"],
        "nodes": [row["name"] for row in result["nodes"]],
        "edges": [
            (row["source"], row["target"], row["kind"])
            for row in result["edges"]
        ],
        "coverage": result["coverage"],
    })


def _canonical_fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _omission_rows(omissions: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"kind": "selection-omission", "reason": name, "count": count}
        for name, count in omissions.items() if count
    ]


def _unavailable(
    query: LineageQuery,
    status: dict[str, Any],
    started: float,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema": "ladon-theorem-lineage-result-v2",
        "operation": "lineage",
        "projection": "closure",
        "status": "unavailable",
        "reason": reason,
        "theorem": query.theorem,
        "authority": "unavailable",
        "evidenceReceipt": lineage_query_receipt(status, query.theorem),
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _NONCLAIM,
    }


_NONCLAIM = (
    "A complete projection covers only the selected stored closure and its recorded "
    "library frontier; it does not prove the theorem or expand library declarations."
)


__all__ = ["query_stored_closure", "refresh_closure_fingerprint"]
