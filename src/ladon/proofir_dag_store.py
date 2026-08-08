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
        if artifact.state != "cataloged" or artifact.artifact_kind != DAG_KIND:
            continue
        try:
            payload = json.loads(artifact.path.read_text(encoding="utf-8"))
            dag_id, nodes, edges = normalize_dag(payload)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            counts["dagOmissions"] += 1
            continue
        connection.execute("INSERT INTO proofir_dags(dag_id,generation_id,artifact_id,schema_version,status,metadata_json) VALUES(?,?,?,?,?,?)",
            (dag_id, generation_id, artifact_ids[artifact.relative_path], int(payload.get("schemaVersion", 2)), "cataloged", _metadata(payload)))
        dag_rows[dag_id] = (artifact.relative_path, artifact.sha256)
        counts["dags"] += 1
        for ordinal, node in enumerate(nodes):
            node_id, kind, status, authority, description, caveat, metadata = node
            connection.execute("INSERT INTO proofir_dag_nodes(node_id,dag_id,node_kind,status,authority,ordinal,description,caveat,metadata_json) VALUES(?,?,?,?,?,?,?,?,?)",
                (node_id, dag_id, kind, status, authority, ordinal, description, caveat, metadata))
            for auth in _authorities(authority):
                connection.execute("INSERT INTO proofir_dag_node_authority(dag_id,node_id,authority) VALUES(?,?,?)", (dag_id,node_id,auth))
                counts["dagAuthorities"] += 1
            counts["dagNodes"] += 1
        for ordinal, edge in enumerate(edges):
            source, target, kind, obligation_id, metadata = edge
            connection.execute("INSERT INTO proofir_dag_edges(dag_id,source_node_id,target_node_id,kind,obligation_id,ordinal,metadata_json) VALUES(?,?,?,?,?,?,?)",
                (dag_id, source, target, kind, obligation_id, ordinal, metadata))
            counts["dagEdges"] += 1
    for artifact in artifacts:
        if artifact.state != "cataloged" or artifact.artifact_kind != WITNESS_KIND:
            continue
        payload = _load(artifact)
        target = str(payload.get("dagId") or payload.get("obligationDagId") or "")
        dag = dag_rows.get(target)
        status = "unmatched"
        if dag is not None:
            named_hash = str(payload.get("dagHash") or payload.get("contentHash") or "").removeprefix("sha256:")
            status = "related" if not named_hash or named_hash == dag[1] else "stale"
            connection.execute("INSERT INTO proofir_dag_witnesses(dag_id,witness_artifact_id,status,guarantee,details_json) VALUES(?,?,?,?,?)",
                (target, artifact_ids[artifact.relative_path], status, str(payload.get("guarantee", "")), _metadata(payload)))
            counts["dagWitnesses"] += 1
    return counts


def normalize_dag(payload: Any) -> tuple[str, list[tuple[str,str,str,str,str,str,str]], list[tuple[str,str,str,str,str]]]:
    if not isinstance(payload, dict) or payload.get("artifactKind") != DAG_KIND:
        raise ValueError("unsupported obligation DAG artifact")
    dag_id = str(payload.get("dagId") or payload.get("id") or "")
    if not dag_id:
        raise ValueError("missing dagId")
    nodes: list[tuple[str,str,str,str,str,str,str]] = []
    seen: dict[str, tuple[str,str,str]] = {}
    for key, kind in (("importedFacts", "imported_fact"), ("obligations", "obligation"), ("producedFacts", "produced_fact")):
        rows = payload.get(key, [])
        if not isinstance(rows, list):
            raise ValueError(f"{key} must be a list")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("node must be an object")
            node_id = str(row.get("id") or row.get("nodeId") or row.get("obligationId") or "")
            if not node_id:
                raise ValueError("node missing id")
            signature = (kind, str(row.get("status", "")), _authority(row.get("authority")))
            if node_id in seen and seen[node_id] != signature:
                raise ValueError(f"conflicting duplicate node: {node_id}")
            if node_id in seen:
                continue
            seen[node_id] = signature
            nodes.append((node_id, kind, signature[1], signature[2], str(row.get("description", "")), str(row.get("caveat", "")), _metadata(row)))
    if len(nodes) > MAX_NODES:
        raise ValueError("node limit exceeded")
    known = set(seen)
    edges: list[tuple[str,str,str,str,str]] = []
    for row in payload.get("edges", []):
        if not isinstance(row, dict):
            raise ValueError("edge must be an object")
        source = str(row.get("source") or row.get("sourceId") or "")
        target = str(row.get("target") or row.get("targetId") or "")
        if source not in known or target not in known:
            raise ValueError(f"missing edge endpoint: {source}->{target}")
        edges.append((source, target, str(row.get("kind", "uses")), str(row.get("obligationId") or row.get("obligation_id") or source), _metadata(row)))
    if len(edges) > MAX_EDGES:
        raise ValueError("edge limit exceeded")
    return dag_id, nodes, edges


def query_dag_routes(connection: sqlite3.Connection, dag_id: str, start: str, end: str | None = None,
                     *, reverse: bool = False, max_depth: int = 64, max_routes: int = 32) -> dict[str, Any]:
    direction = "target_node_id" if reverse else "source_node_id"
    other = "source_node_id" if reverse else "target_node_id"
    sql = f"""WITH RECURSIVE walk(node_id, depth, path) AS (
      SELECT ?, 0, '|' || ? || '|'
      UNION ALL
      SELECT e.{other}, walk.depth + 1, walk.path || e.{other} || '|'
      FROM walk JOIN proofir_dag_edges e ON e.dag_id = ? AND e.{direction} = walk.node_id
      WHERE walk.depth < ? AND instr(walk.path, '|' || e.{other} || '|') = 0
    ) SELECT w.node_id,w.depth,n.node_kind,n.status,n.authority,n.description FROM walk w
      JOIN proofir_dag_nodes n ON n.dag_id = ? AND n.node_id = w.node_id
      ORDER BY w.depth,w.node_id LIMIT ?"""
    rows = [dict(zip(("nodeId","depth","kind","status","authority","description"), row)) for row in connection.execute(sql, (start,start,dag_id,max_depth,dag_id,max_routes))]
    return {"schema": "ladon-proofir-dag-route-v1", "dagId": dag_id, "start": start, "end": end, "reverse": reverse, "routes": rows, "truncated": len(rows) >= max_routes}


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
