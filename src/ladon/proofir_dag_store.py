"""Bounded, SQL-owned persistence and traversal for ProofIR obligation DAGs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any, Mapping

from ladon.proofir_catalog import CatalogArtifact

DAG_KIND = "proof_ir_v2_obligation_dag"
WITNESS_KIND = "proof_ir_v2_obligation_dag_check_witness"
MAX_NODES = 10_000
MAX_EDGES = 30_000


def insert_dag_evidence(connection: sqlite3.Connection, generation_id: str,
                        artifacts: tuple[CatalogArtifact, ...], artifact_ids: Mapping[str, str]) -> dict[str, int]:
    counts = {"dags": 0, "dagNodes": 0, "dagEdges": 0, "dagAuthorities": 0, "dagWitnesses": 0, "dagOmissions": 0}
    dag_rows: dict[str, tuple[str, str]] = {}
    for artifact in artifacts:
        if artifact.state == "cataloged" and artifact.artifact_kind == DAG_KIND:
            if _insert_one_dag(connection, generation_id, artifact, artifact_ids, counts, dag_rows):
                counts["dags"] += 1
    for artifact in artifacts:
        if artifact.state == "cataloged" and artifact.artifact_kind == WITNESS_KIND:
            counts["dagWitnesses"] += _insert_one_witness(connection, artifact, artifact_ids, dag_rows)
    return counts


def _insert_one_dag(connection: sqlite3.Connection, generation_id: str, artifact: CatalogArtifact,
                    artifact_ids: Mapping[str, str], counts: dict[str, int], dag_rows: dict[str, tuple[str, str]]) -> bool:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        dag_id, nodes, edges = normalize_dag(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        counts["dagOmissions"] += 1
        return False
    connection.execute("INSERT INTO proofir_dags(dag_id,generation_id,artifact_id,schema_version,status,metadata_json) VALUES(?,?,?,?,?,?)",
        (dag_id, generation_id, artifact_ids[artifact.relative_path], int(payload.get("schemaVersion", 2)), "cataloged", _metadata(payload)))
    dag_rows[dag_id] = (artifact.relative_path, artifact.sha256)
    _insert_nodes(connection, dag_id, nodes, counts)
    _insert_edges(connection, dag_id, edges, counts)
    return True


def _insert_nodes(connection: sqlite3.Connection, dag_id: str, nodes: list[tuple[str,str,str,str,str,str,str]], counts: dict[str, int]) -> None:
    for ordinal, node in enumerate(nodes):
        node_id, kind, status, authority, description, caveat, metadata = node
        connection.execute("INSERT INTO proofir_dag_nodes(node_id,dag_id,node_kind,status,authority,ordinal,description,caveat,metadata_json) VALUES(?,?,?,?,?,?,?,?,?)",
            (node_id, dag_id, kind, status, authority, ordinal, description, caveat, metadata))
        authorities = _authorities(authority)
        connection.executemany("INSERT INTO proofir_dag_node_authority(dag_id,node_id,authority) VALUES(?,?,?)",
            ((dag_id, node_id, auth) for auth in authorities))
        counts["dagAuthorities"] += len(authorities)
        counts["dagNodes"] += 1


def _insert_edges(connection: sqlite3.Connection, dag_id: str, edges: list[tuple[str,str,str,str,str]], counts: dict[str, int]) -> None:
    for ordinal, edge in enumerate(edges):
        source, target, kind, obligation_id, metadata = edge
        connection.execute("INSERT INTO proofir_dag_edges(dag_id,source_node_id,target_node_id,kind,obligation_id,ordinal,metadata_json) VALUES(?,?,?,?,?,?,?)",
            (dag_id, source, target, kind, obligation_id, ordinal, metadata))
        counts["dagEdges"] += 1


def _insert_one_witness(connection: sqlite3.Connection, artifact: CatalogArtifact, artifact_ids: Mapping[str, str], dag_rows: Mapping[str, tuple[str, str]]) -> int:
    payload = _load(artifact)
    target = str(payload.get("dagId") or payload.get("obligationDagId") or "")
    dag = dag_rows.get(target)
    if dag is None:
        return 0
    named_hash = str(payload.get("dagHash") or payload.get("contentHash") or "").removeprefix("sha256:")
    status = "related" if not named_hash or named_hash == dag[1] else "stale"
    connection.execute("INSERT INTO proofir_dag_witnesses(dag_id,witness_artifact_id,status,guarantee,details_json) VALUES(?,?,?,?,?)",
        (target, artifact_ids[artifact.relative_path], status, str(payload.get("guarantee", "")), _metadata(payload)))
    return 1


def normalize_dag(payload: Any) -> tuple[str, list[tuple[str,str,str,str,str,str,str]], list[tuple[str,str,str,str,str]]]:
    if not isinstance(payload, dict) or payload.get("artifactKind") != DAG_KIND:
        raise ValueError("unsupported obligation DAG artifact")
    dag_id = str(payload.get("dagId") or payload.get("id") or "")
    if not dag_id:
        raise ValueError("missing dagId")
    nodes, seen = _normalize_nodes(payload)
    if len(nodes) > MAX_NODES:
        raise ValueError("node limit exceeded")
    known = set(seen)
    edges = _normalize_edges(payload, known)
    if len(edges) > MAX_EDGES:
        raise ValueError("edge limit exceeded")
    return dag_id, nodes, edges


def _normalize_nodes(payload: dict[str, Any]) -> tuple[list[tuple[str,str,str,str,str,str,str]], dict[str, tuple[str,str,str]]]:
    nodes: list[tuple[str,str,str,str,str,str,str]] = []
    seen: dict[str, tuple[str,str,str]] = {}
    for key, kind in (("importedFacts", "imported_fact"), ("obligations", "obligation"), ("producedFacts", "produced_fact")):
        rows = payload.get(key, [])
        if not isinstance(rows, list):
            raise ValueError(f"{key} must be a list")
        for row in rows:
            node = _normalize_node(row, kind, seen)
            if node is not None:
                nodes.append(node)
    return nodes, seen


def _normalize_node(row: Any, kind: str, seen: dict[str, tuple[str,str,str]]) -> tuple[str,str,str,str,str,str,str] | None:
    if not isinstance(row, dict):
        raise ValueError("node must be an object")
    node_id = str(row.get("id") or row.get("nodeId") or row.get("obligationId") or "")
    if not node_id:
        raise ValueError("node missing id")
    signature = (kind, str(row.get("status", "")), _authority(row.get("authority")))
    if node_id in seen and seen[node_id] != signature:
        raise ValueError(f"conflicting duplicate node: {node_id}")
    if node_id in seen:
        return None
    seen[node_id] = signature
    return (node_id, kind, signature[1], signature[2], str(row.get("description", "")), str(row.get("caveat", "")), _metadata(row))


def _normalize_edges(payload: dict[str, Any], known: set[str]) -> list[tuple[str,str,str,str,str]]:
    return [edge for row in payload.get("edges", []) if (edge := _normalize_edge(row, known)) is not None]


def _normalize_edge(row: Any, known: set[str]) -> tuple[str, str, str, str, str] | None:
    if not isinstance(row, dict):
        raise ValueError("edge must be an object")
    source = str(row.get("source") or row.get("sourceId") or "")
    target = str(row.get("target") or row.get("targetId") or "")
    if source not in known or target not in known:
        raise ValueError(f"missing edge endpoint: {source}->{target}")
    return (source, target, str(row.get("kind", "uses")), str(row.get("obligationId") or row.get("obligation_id") or source), _metadata(row))


def query_dag_routes(connection: sqlite3.Connection, dag_id: str, start: str, end: str | None = None,
                     *, reverse: bool = False, max_depth: int = 64, max_routes: int = 32,
                     max_output_bytes: int = 1_000_000) -> dict[str, Any]:
    """Return endpoint-correct bounded paths plus a compatibility node projection."""
    _validate_route_bounds(max_depth, max_routes, max_output_bytes)
    direction = "target_node_id" if reverse else "source_node_id"
    other = "source_node_id" if reverse else "target_node_id"
    sql = f"""WITH RECURSIVE walk(node_id, depth, node_path, edge_path, visited) AS (
      SELECT ?, 0, ?, '', ?
      UNION ALL
      SELECT e.{other}, walk.depth + 1,
             walk.node_path || ? || e.{other},
             CASE WHEN walk.edge_path = '' THEN e.source_node_id || ? || e.target_node_id || ? || e.kind || ? || e.obligation_id
                  ELSE walk.edge_path || ? || e.source_node_id || ? || e.target_node_id || ? || e.kind || ? || e.obligation_id END,
             walk.visited || e.{other} || ?
      FROM walk JOIN proofir_dag_edges e ON e.dag_id = ? AND e.{direction} = walk.node_id
      WHERE walk.depth < ? AND instr(walk.visited, ? || e.{other} || ?) = 0
    ) SELECT node_id, depth, node_path, edge_path FROM walk
      WHERE (? IS NULL OR node_id = ?) ORDER BY depth, node_path LIMIT ?"""
    separator = "\x1f"
    edge_separator = "\x1e"
    rows = connection.execute(
        sql,
        (start, start, f"{separator}{start}{separator}", separator,
         separator, separator, separator, edge_separator,
         separator, separator, separator, separator,
         dag_id, max_depth, separator, separator, end, end, max_routes + 1),
    ).fetchall()
    truncated = len(rows) > max_routes
    selected = rows[:max_routes]
    paths = _materialize_paths(connection, dag_id, selected, reverse=reverse)
    result: dict[str, Any] = {
        "schema": "ladon-proofir-obligation-routes-v1",
        "dagId": dag_id,
        "start": start,
        "end": end,
        "reverse": reverse,
        "minimumDepth": min((path["depth"] for path in paths), default=None),
        "reachable": bool(paths),
        "paths": paths,
        "selectedSubgraph": _selected_subgraph(paths),
        "transitions": _transitions(paths),
        "diagnostics": [],
        "coverage": {"matched": len(rows), "returned": len(paths), "cap": max_routes},
        "truncated": truncated,
        "nonclaims": ["ProofIR obligation routes are not Lean declaration dependencies or proof-term verification."],
    }
    # Keep the original flat field for current callers while new callers use paths.
    result["routes"] = paths[0]["nodes"] if end is not None and paths else _legacy_nodes(connection, dag_id, selected)
    _enforce_output_bytes(result, max_output_bytes)
    return result


def _validate_route_bounds(max_depth: int, max_routes: int, max_output_bytes: int) -> None:
    if min(max_depth, max_routes, max_output_bytes) < 1:
        raise ValueError("route bounds must be positive")


def _materialize_paths(connection: sqlite3.Connection, dag_id: str, rows: list[tuple[Any, ...]], *, reverse: bool) -> list[dict[str, Any]]:
    paths = []
    for index, (_, depth, node_path, edge_path) in enumerate(rows, start=1):
        node_ids = tuple(node_path.split("\x1f"))
        edge_ids = tuple(edge_path.split("\x1e")) if edge_path else ()
        nodes = _node_rows(connection, dag_id, node_ids)
        edges = _edge_rows(connection, dag_id, edge_ids, reverse=reverse)
        paths.append({"pathId": f"path-{index:04d}", "depth": depth, "nodes": nodes, "edges": edges})
    return paths


def _node_rows(connection: sqlite3.Connection, dag_id: str, node_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    result = []
    for node_id in node_ids:
        row = connection.execute("SELECT node_id,node_kind,status,authority,description FROM proofir_dag_nodes WHERE dag_id=? AND node_id=?", (dag_id, node_id)).fetchone()
        if row:
            result.append({"nodeId": row[0], "kind": row[1], "status": row[2], "authority": row[3], "description": row[4]})
    return result


def _edge_rows(connection: sqlite3.Connection, dag_id: str, edge_ids: tuple[str, ...], *, reverse: bool) -> list[dict[str, Any]]:
    result = []
    for encoded in edge_ids:
        source, target, kind, obligation = encoded.split("\x1f", 3)
        result.append({"sourceNodeId": source, "targetNodeId": target, "kind": kind, "obligationId": obligation, "direction": "reverse" if reverse else "forward"})
    return result


def _selected_subgraph(paths: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    nodes = {row["nodeId"]: row for path in paths for row in path["nodes"]}
    edges = {(row["sourceNodeId"], row["targetNodeId"], row["kind"], row["obligationId"]): row for path in paths for row in path["edges"]}
    return {"nodes": [nodes[key] for key in sorted(nodes)], "edges": [edges[key] for key in sorted(edges)]}


def _transitions(paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions = []
    for path in paths:
        previous = None
        for node in path["nodes"]:
            current = (node["status"], node["authority"])
            if previous is not None and current != previous:
                transitions.append({"pathId": path["pathId"], "from": previous, "to": current, "nodeId": node["nodeId"]})
            previous = current
    return transitions


def _legacy_nodes(connection: sqlite3.Connection, dag_id: str, rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    ids = tuple(dict.fromkeys(node for row in rows for node in row[2].split("\x1f")))
    return _node_rows(connection, dag_id, ids)


def _enforce_output_bytes(result: dict[str, Any], limit: int) -> None:
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > limit:
        raise ValueError(f"route output exceeds byte limit: {len(encoded)} > {limit}")


def _load(artifact: CatalogArtifact) -> dict[str, Any]:
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}

def _authority(value: Any) -> str:
    if isinstance(value, list): return ",".join(sorted(str(x) for x in value))
    return str(value or "")

def _authorities(value: str) -> tuple[str, ...]: return tuple(x for x in value.split(",") if x) or ("unknown",)

def _metadata(value: Mapping[str, Any]) -> str:
    raw = json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    return raw if len(raw.encode()) <= 16 * 1024 else json.dumps({"truncated": True, "sha256": hashlib.sha256(raw.encode()).hexdigest()}, sort_keys=True)
