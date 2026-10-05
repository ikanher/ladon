"""Bounded indexed candidate explanation transport."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.proof_difference import DifferenceRequest, analyze_difference
from ladon.proof_search_index import default_proof_search_index_path, inspect_proof_search_index


def dispatch_explain(args: Any, repo_root: Path, index_path: Path | None) -> Mapping[str, Any]:
    if getattr(args, "check_artifact", None):
        from ladon.stored_candidate_type import explain_stored_candidate

        return explain_stored_candidate(args, repo_root)
    request = DifferenceRequest(args.goal, args.candidate, args.module, tuple(args.assumption), args.suggestion_cap, args.freshness, args.raw_signature)
    path = index_path or default_proof_search_index_path(repo_root)
    freshness = _freshness(args, repo_root, index_path)
    if args.freshness == "verify" and freshness.get("freshness") != "fresh":
        return unavailable(args, "candidate index is stale or unavailable", freshness)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        if args.freshness == "stored":
            freshness.update(_stored_generation(connection))
        rows = _lookup_candidates(connection, args)
    matches = [candidate_match(row, freshness) for row in rows[: args.suggestion_cap]]
    if len(rows) != 1:
        return unavailable(args, _lookup_reason(rows, args.suggestion_cap), freshness, matches, len(rows) > args.suggestion_cap)
    row = rows[0]
    reason = _type_unavailable_reason(row)
    if reason:
        return unavailable(args, reason, freshness, matches)
    evidence = candidate_match(row, freshness)
    evidence.update(freshness=args.freshness, freshnessEvidence=freshness)
    return analyze_difference(request, candidate_signature=str(row[3]), candidate_evidence=evidence)


def _lookup_candidates(connection: sqlite3.Connection, args: Any) -> list[sqlite3.Row]:
    owner = " AND module=?" if args.module else ""
    parameters = (args.candidate, args.candidate)
    if args.module:
        parameters += (args.module,)
    return connection.execute(
        "SELECT id,name,candidate_name,type_text,type_text_bytes,type_status,authority,module,"
        "namespace,package,path,line,type_text_truncated FROM declarations "
        f"WHERE (name=? OR candidate_name=?){owner} ORDER BY path,line,id LIMIT ?",
        (*parameters, args.suggestion_cap + 1),
    ).fetchall()


def _type_unavailable_reason(row: sqlite3.Row) -> str | None:
    if not isinstance(row[3], str) or not row[3].strip():
        return "candidate type text is missing or empty"
    if row[12]:
        return "candidate type text is truncated"
    if row[5] != "lean-rendered":
        return "indexed type is not structurally rendered"
    return None


def _stored_generation(connection: sqlite3.Connection) -> dict[str, Any]:
    """Read stored identities without inspecting source files or invoking Lean."""
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='metadata' AND type='table'").fetchone():
        return {"reason": "stored generation metadata is unavailable"}
    fields = ("generationIdentity", "helperIdentity", "indexSchema", "sourceFingerprint",
              "configurationFingerprint", "toolchainIdentity")
    placeholders = ",".join("?" for _ in fields)
    return dict(connection.execute(f"SELECT key,value FROM metadata WHERE key IN ({placeholders})", fields))


def _freshness(args: Any, repo_root: Path, index_path: Path | None) -> dict[str, Any]:
    if args.freshness == "stored":
        return {"freshness": "stored"}
    status = inspect_proof_search_index(repo_root, index_path=index_path, verify_sources=True)
    # Keep navigation identity and limitations beside the candidate; the index
    # status command owns storage diagnostics, which grow with the schema.
    fields = (
        "freshness", "status", "indexPath", "indexSchema", "generationIdentity",
        "currentGenerationIdentity", "sourceFingerprint", "configurationFingerprint",
        "toolchainIdentity", "helperIdentity", "evidenceStatus", "nonclaim", "reason",
    )
    return {key: status[key] for key in fields if key in status}


def _lookup_reason(rows: Sequence[Any], cap: int) -> str:
    if not rows:
        return "candidate declaration was not found"
    if len(rows) > cap:
        return "candidate declaration matches exceed the bounded cap"
    return "candidate declaration is not unique"


def candidate_match(row: Any, freshness: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "declarationId": row[0], "name": row[1], "candidateName": row[2],
        "typeText": row[3], "typeTextBytes": row[4], "typeStatus": row[5],
        "authority": row[6], "module": row[7], "namespace": row[8],
        "package": row[9], "path": row[10], "line": row[11],
        "typeTextTruncated": bool(row[12]), "generationEvidence": dict(freshness),
    }


def unavailable(args: Any, reason: str, freshness: Mapping[str, Any], matches: Sequence[Mapping[str, Any]] = (), truncated: bool = False) -> dict[str, Any]:
    return {
        "schema": "ladon-proof-difference-result-v1", "schemaVersion": 2,
        "operation": "explain", "status": "unavailable", "reason": reason,
        "goal": args.goal, "candidate": args.candidate,
        "candidateMatches": [dict(row) for row in matches],
        "candidateMatchesTruncated": truncated, "freshnessEvidence": dict(freshness),
        "nonclaims": [
            "Indexed type text does not establish Lean applicability or proof verification.",
            "Use proof-search check or discover for explicit Lean candidate checking.",
        ],
    }


__all__ = ["candidate_match", "dispatch_explain", "unavailable"]
