"""Public render-neutral queries over stored ProofIR evidence."""
from __future__ import annotations
import sqlite3
from typing import Any
from ladon.proofir_dag_store import query_dag_routes

def query_theorem_evidence(connection: sqlite3.Connection, theorem: str, limit: int = 100) -> dict[str, Any]:
    rows = [dict(row) for row in connection.execute("SELECT s.surface_id,s.declaration_name,s.source_path,s.status,s.authority_json,s.proof_trust,s.replay_boundary_json,a.declaration_id,a.confidence,a.freshness FROM proofir_surfaces s LEFT JOIN proofir_attachments a ON a.surface_row_id=s.surface_row_id WHERE s.declaration_name=? ORDER BY s.surface_id LIMIT ?", (theorem, limit))]
    return {"schema": "ladon-proofir-theorem-evidence-v1", "theorem": theorem, "surfaces": rows, "nonclaims": ["ProofIR surface evidence is not Lean proof-term verification"]}

def query_artifact_evidence(connection: sqlite3.Connection, artifact: str, limit: int = 100) -> dict[str, Any]:
    rows = [dict(row) for row in connection.execute("SELECT path,artifact_kind,state,sha256,byte_size,diagnostic FROM proofir_artifacts WHERE path=? OR artifact_id=? LIMIT ?", (artifact, artifact, limit))]
    return {"schema": "ladon-proofir-artifact-evidence-v1", "artifact": artifact, "artifacts": rows}

__all__ = ["query_theorem_evidence", "query_artifact_evidence", "query_dag_routes"]
