"""Read-only, render-neutral projections over stored ProofIR evidence."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from ladon.proofir_dag_store import query_dag_routes
from ladon.proofir_coverage import query_proofir_coverage

THEOREM_DOSSIER_SCHEMA = "ladon-proofir-theorem-dossier-v1"


@dataclass(frozen=True)
class EvidenceQueryBounds:
    """Validated per-section and serialized-output limits."""

    surfaces: int = 100
    claims: int = 100
    replay: int = 100
    context: int = 100
    diagnostics: int = 100
    max_output_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        if min(self.surfaces, self.claims, self.replay, self.context, self.diagnostics, self.max_output_bytes) < 1:
            raise ValueError("evidence query bounds must be positive")


def query_theorem_dossier(
    connection: sqlite3.Connection,
    theorem: str,
    *,
    bounds: EvidenceQueryBounds | None = None,
) -> dict[str, Any]:
    """Build one bounded theorem dossier without executing external tools."""
    bounds = bounds or EvidenceQueryBounds()
    declarations = _declarations(connection, theorem)
    selected = {str(row["declarationId"]) for row in declarations if row["selected"]}
    surfaces = _surfaces(connection, theorem, selected, bounds.surfaces)
    claims = _claims(connection, surfaces, bounds.claims)
    replay = _replay(connection, surfaces, bounds.replay)
    context = _obligation_context(connection, claims, bounds.context)
    diagnostics = _diagnostics(connection, surfaces, bounds.diagnostics)
    lineage = _lineage(connection, theorem)
    result: dict[str, Any] = {
        "schema": THEOREM_DOSSIER_SCHEMA,
        "theorem": theorem,
        "declaration": {"candidates": declarations, "selectedCount": len(selected)},
        "attachments": [row for row in surfaces if row.get("attachment") is not None],
        "surfaces": _bounded_section(surfaces, bounds.surfaces),
        "claims": _bounded_section(claims, bounds.claims),
        "replay": _bounded_section(replay, bounds.replay),
        "obligationContext": context,
        "lineage": lineage,
        "diagnostics": _bounded_section(diagnostics, bounds.diagnostics),
        "coverage": _coverage(connection, theorem, declarations, surfaces, claims, replay, lineage),
        "nonclaims": [
            "ProofIR claims, replay observations, and obligation routes are quoted evidence, not Lean proof-term verification.",
            "Observed absence is bounded by the configured and inspected project-local evidence population.",
        ],
    }
    _enforce_output_bytes(result, bounds.max_output_bytes)
    return result


def query_theorem_evidence(connection: sqlite3.Connection, theorem: str, limit: int = 100) -> dict[str, Any]:
    """Compatibility projection retaining the earlier theorem query shape."""
    dossier = query_theorem_dossier(connection, theorem, bounds=EvidenceQueryBounds(surfaces=limit, claims=limit, replay=limit, diagnostics=limit))
    return {"schema": dossier["schema"], "theorem": theorem, "surfaces": dossier["surfaces"], "nonclaims": dossier["nonclaims"]}


def query_artifact_evidence(connection: sqlite3.Connection, artifact: str, limit: int = 100) -> dict[str, Any]:
    rows = [dict(row) for row in connection.execute("SELECT path,artifact_kind,state,sha256,byte_size,diagnostic FROM proofir_artifacts WHERE path=? OR artifact_id=? ORDER BY path LIMIT ?", (artifact, artifact, limit))]
    return {"schema": "ladon-proofir-artifact-evidence-v1", "artifact": artifact, "artifacts": rows}


def _declarations(connection: sqlite3.Connection, theorem: str) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT id,name,candidate_name,namespace,kind,module,package,path,line,authority FROM declarations WHERE name=? OR candidate_name=? ORDER BY path,line,id", (theorem, theorem)).fetchall()
    result = []
    for row in rows:
        declaration_id = str(row[0])
        count = int(connection.execute("SELECT COUNT(*) FROM proofir_attachments WHERE declaration_id=?", (declaration_id,)).fetchone()[0])
        result.append({"declarationId": declaration_id, "name": row[1], "candidateName": row[2], "namespace": row[3], "kind": row[4], "module": row[5], "package": row[6], "path": row[7], "line": row[8], "authority": row[9], "selected": count == 1})
    if sum(row["selected"] for row in result) > 1:
        for row in result:
            row["selected"] = False
    return result


def _surfaces(connection: sqlite3.Connection, theorem: str, declaration_ids: set[str], limit: int) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT s.surface_row_id,s.artifact_id,s.surface_id,s.claim_id,s.declaration_name,s.source_path,s.status,s.authority_json,s.proof_trust,s.replay_boundary_json,a.declaration_id,a.method,a.confidence,a.freshness FROM proofir_surfaces s LEFT JOIN proofir_attachments a ON a.surface_row_id=s.surface_row_id WHERE s.declaration_name=? ORDER BY s.surface_id LIMIT ?", (theorem, limit + 1)).fetchall()
    result = []
    for row in rows:
        attachment = None
        if row[10] in declaration_ids:
            attachment = {"declarationId": row[10], "method": row[11], "confidence": row[12], "freshness": row[13]}
        result.append({"surfaceRowId": row[0], "artifactId": row[1], "surfaceId": row[2], "claimId": row[3], "declarationName": row[4], "sourcePath": row[5], "status": row[6], "authority": _parse_json(row[7]), "proofTrust": row[8], "replayBoundary": _parse_json(row[9]), "attachment": attachment})
    return result


def _claims(connection: sqlite3.Connection, surfaces: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    result = []
    for surface in surfaces[:limit]:
        rows = connection.execute("SELECT c.claim_row_id,c.claim_id,c.status,c.authority_json,c.scope,c.proof_trust,c.replay_boundary_json,c.extractor_guarantee FROM proofir_claims c WHERE c.artifact_id=? AND (c.claim_id=? OR EXISTS (SELECT 1 FROM proofir_surface_claims sc WHERE sc.claim_row_id=c.claim_row_id AND sc.surface_row_id=?)) ORDER BY c.claim_id LIMIT ?", (surface["artifactId"], surface["claimId"] or "", surface["surfaceRowId"], limit + 1)).fetchall()
        result.extend({"claimRowId": row[0], "claimId": row[1], "status": row[2], "authority": _parse_json(row[3]), "scope": row[4], "proofTrust": row[5], "replayBoundary": _parse_json(row[6]), "extractorGuarantee": row[7], "surfaceId": surface["surfaceId"]} for row in rows)
    return _dedupe(result, "claimRowId")[:limit]


def _replay(connection: sqlite3.Connection, surfaces: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    artifacts = {surface["artifactId"] for surface in surfaces}
    if not artifacts:
        return []
    placeholders = ",".join("?" for _ in artifacts)
    rows = connection.execute(f"SELECT r.replay_id,r.artifact_id,r.provenance_id,r.module,r.return_code,r.guarantee,r.authority_json,rs.surface_id,rs.status,rs.diagnostic FROM proofir_replay_runs r JOIN proofir_relations rel ON rel.source_artifact_id=r.artifact_id AND rel.kind='replays' JOIN proofir_replay_surfaces rs ON rs.replay_id=r.replay_id WHERE rel.target_artifact_id IN ({placeholders}) ORDER BY r.replay_id,rs.surface_id LIMIT ?", (*sorted(artifacts), limit + 1)).fetchall()
    return [{"replayId": row[0], "artifactId": row[1], "provenanceId": row[2], "module": row[3], "returnCode": row[4], "guarantee": row[5], "authority": _parse_json(row[6]), "surfaceId": row[7], "surfaceStatus": row[8], "diagnostic": row[9]} for row in rows]


def _obligation_context(connection: sqlite3.Connection, claims: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    claim_ids = sorted({str(claim["claimId"]) for claim in claims if claim.get("claimId")})
    if not claim_ids:
        return {"status": "not-observed", "nodes": [], "edges": []}
    placeholders = ",".join("?" for _ in claim_ids)
    nodes = connection.execute(f"SELECT dag_id,node_id,node_kind,status,authority,description FROM proofir_dag_nodes WHERE node_id IN ({placeholders}) ORDER BY dag_id,node_id LIMIT ?", (*claim_ids, limit + 1)).fetchall()
    if not nodes:
        return {"status": "not-observed", "nodes": [], "edges": []}
    dag_ids = sorted({row[0] for row in nodes})
    edges = _context_edges(connection, dag_ids, claim_ids, limit)
    return {"status": "observed", "nodes": [{"dagId": row[0], "nodeId": row[1], "kind": row[2], "status": row[3], "authority": row[4], "description": row[5]} for row in nodes[:limit]], "edges": [{"dagId": row[0], "sourceNodeId": row[1], "targetNodeId": row[2], "kind": row[3], "obligationId": row[4]} for row in edges[:limit]], "matched": len(nodes), "truncated": len(nodes) > limit or len(edges) > limit}


def _context_edges(connection: sqlite3.Connection, dag_ids: list[str], claim_ids: list[str], limit: int) -> list[sqlite3.Row]:
    dag_placeholders = ",".join("?" for _ in dag_ids)
    claim_placeholders = ",".join("?" for _ in claim_ids)
    sql = f"SELECT dag_id,source_node_id,target_node_id,kind,obligation_id FROM proofir_dag_edges WHERE dag_id IN ({dag_placeholders}) AND (source_node_id IN ({claim_placeholders}) OR target_node_id IN ({claim_placeholders}) OR obligation_id IN ({claim_placeholders})) ORDER BY dag_id,source_node_id,target_node_id LIMIT ?"
    return connection.execute(sql, (*dag_ids, *claim_ids, *claim_ids, *claim_ids, limit + 1)).fetchall()


def _diagnostics(connection: sqlite3.Connection, surfaces: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    artifact_ids = sorted({surface["artifactId"] for surface in surfaces})
    if not artifact_ids:
        return []
    placeholders = ",".join("?" for _ in artifact_ids)
    rows = connection.execute(f"SELECT diagnostic_id,artifact_id,kind,subject,reason,details_json FROM proofir_diagnostics WHERE artifact_id IN ({placeholders}) ORDER BY reason,subject LIMIT ?", (*artifact_ids, limit + 1)).fetchall()
    return [{"diagnosticId": row[0], "artifactId": row[1], "kind": row[2], "subject": row[3], "reason": row[4], "details": _parse_json(row[5])} for row in rows]


def _lineage(connection: sqlite3.Connection, theorem: str) -> dict[str, Any]:
    row = connection.execute("SELECT closure_id,semantic_closure_fingerprint,repository,source_fingerprint,configuration_fingerprint,toolchain_identity,helper_identity,base_generation_identity,schema_generation,authority,semantic_status FROM lineage_closures WHERE theorem_name=? AND active=1 ORDER BY closure_id LIMIT 1", (theorem,)).fetchone()
    if row is None:
        return {"status": "unavailable", "closures": []}
    return {"status": "fresh", "closures": [{"closureId": row[0], "fingerprint": row[1], "repository": row[2], "sourceFingerprint": row[3], "configurationFingerprint": row[4], "toolchainIdentity": row[5], "helperIdentity": row[6], "baseGenerationIdentity": row[7], "schemaGeneration": row[8], "authority": row[9], "semanticStatus": row[10]}]}


def _coverage(connection: sqlite3.Connection, theorem: str, declarations: list[dict[str, Any]], surfaces: list[dict[str, Any]], claims: list[dict[str, Any]], replay: list[dict[str, Any]], lineage: dict[str, Any]) -> dict[str, Any]:
    coverage = query_proofir_coverage(connection, theorem=theorem)
    coverage.update({"declarations": len(declarations), "surfaces": len(surfaces), "claims": len(claims), "replay": len(replay), "lineage": lineage["status"]})
    return coverage


def _bounded_section(rows: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    return {"rows": rows[:limit], "matched": len(rows), "returned": min(len(rows), limit), "truncated": len(rows) > limit, "cap": limit}


def _dedupe(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return list({str(row[key]): row for row in rows}.values())


def _parse_json(value: Any) -> Any:
    try:
        return json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        return {"quoted": value, "malformed": True}


def _enforce_output_bytes(result: dict[str, Any], limit: int) -> None:
    if len(json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")) > limit:
        raise ValueError("theorem dossier exceeds output byte limit")


__all__ = ["EvidenceQueryBounds", "query_theorem_dossier", "query_theorem_evidence", "query_artifact_evidence", "query_dag_routes"]
