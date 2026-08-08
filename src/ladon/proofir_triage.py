"""Bounded repository-wide ProofIR evidence-health findings."""

from __future__ import annotations

import sqlite3
from typing import Any

from ladon.proofir_coverage import query_proofir_coverage


def query_proofir_triage(connection: sqlite3.Connection, *, limit: int = 100) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("triage limit must be positive")
    families = {
        "unattached_surface": _unattached(connection, limit),
        "ambiguous_attachment": _ambiguous(connection, limit),
        "stale_attachment": _stale(connection, limit),
        "replay_issue": _replay_issues(connection, limit),
        "stale_witness": _stale_witness(connection, limit),
        "unsupported_artifact": _artifact_states(connection, limit),
        "disconnected_evidence": _disconnected(connection, limit),
    }
    findings = [dict(row, ruleId=family) for family, rows in families.items() for row in rows]
    findings.sort(key=lambda row: (str(row["ruleId"]), str(row.get("subject", "")), str(row.get("identity", ""))))
    return {"schema": "ladon-proofir-repository-triage-v1", "families": {key: {"rows": value, "returned": len(value), "cap": limit, "truncated": len(value) >= limit} for key, value in families.items()}, "findings": findings[:limit], "coverage": query_proofir_coverage(connection), "nonclaims": ["Triage findings are review advice, not Lean theorem truth or automatic proof defects."]}


def _unattached(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], sourcePath=row[2], reason="no-selected-attachment") for row in connection.execute("SELECT s.surface_id,s.declaration_name,s.source_path FROM proofir_surfaces s LEFT JOIN proofir_attachments a ON a.surface_row_id=s.surface_row_id WHERE a.surface_row_id IS NULL ORDER BY s.surface_id LIMIT ?", (limit,))]


def _ambiguous(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], reason="competing-candidates") for row in connection.execute("SELECT surface_row_id,COUNT(*) FROM proofir_attachment_candidates GROUP BY surface_row_id HAVING COUNT(*) > 1 ORDER BY surface_row_id LIMIT ?", (limit,))]


def _stale(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], reason="stale-source") for row in connection.execute("SELECT surface_row_id,declaration_id FROM proofir_attachments WHERE freshness='stale' ORDER BY surface_row_id LIMIT ?", (limit,))]


def _replay_issues(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], reason="failed-replay" if row[2] else "stale-or-foreign-surface") for row in connection.execute("SELECT replay_id,surface_id,return_code FROM proofir_replay_runs r LEFT JOIN proofir_replay_surfaces s USING(replay_id) WHERE r.return_code != 0 OR s.status IN ('stale','foreign') ORDER BY replay_id LIMIT ?", (limit,))]


def _stale_witness(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], reason=row[2]) for row in connection.execute("SELECT witness_artifact_id,dag_id,status FROM proofir_dag_witnesses WHERE status != 'related' ORDER BY witness_artifact_id LIMIT ?", (limit,))]


def _artifact_states(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], reason=row[2]) for row in connection.execute("SELECT artifact_id,path,state FROM proofir_artifacts WHERE state != 'cataloged' ORDER BY path LIMIT ?", (limit,))]


def _disconnected(connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return [dict(identity=row[0], subject=row[1], reason="no-current-declaration") for row in connection.execute("SELECT surface_id,declaration_name FROM proofir_surfaces WHERE declaration_name != '' AND NOT EXISTS (SELECT 1 FROM declarations d WHERE d.name=proofir_surfaces.declaration_name) ORDER BY surface_id LIMIT ?", (limit,))]


__all__ = ["query_proofir_triage"]
