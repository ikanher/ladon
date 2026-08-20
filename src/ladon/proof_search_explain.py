"""Bounded indexed candidate explanation transport."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.proof_difference import DifferenceRequest, analyze_difference
from ladon.proof_search_index import default_proof_search_index_path, inspect_proof_search_index


def dispatch_explain(args: Any, repo_root: Path, index_path: Path | None) -> Mapping[str, Any]:
    request = DifferenceRequest(args.goal, args.candidate, args.module, tuple(args.assumption), args.suggestion_cap, args.freshness, args.raw_signature)
    path = index_path or default_proof_search_index_path(repo_root)
    freshness = _freshness(args, repo_root, index_path)
    if args.freshness == "verify" and freshness.get("freshness") != "fresh":
        return unavailable(args, "candidate index is stale or unavailable", freshness)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id,name,candidate_name,type_text,type_text_bytes,type_status,authority,module,"
            "namespace,package,path,line,type_text_truncated FROM declarations "
            "WHERE name=? OR candidate_name=? ORDER BY path,line,id LIMIT ?",
            (args.candidate, args.candidate, args.suggestion_cap + 1),
        ).fetchall()
    matches = [candidate_match(row, freshness) for row in rows[: args.suggestion_cap]]
    if len(rows) != 1:
        return unavailable(args, _lookup_reason(rows, args.suggestion_cap), freshness, matches, len(rows) > args.suggestion_cap)
    row = rows[0]
    if row[12]:
        return unavailable(args, "candidate type text is truncated", freshness, matches)
    if row[5] != "lean-rendered":
        return unavailable(args, "indexed type is not structurally rendered", freshness, matches)
    evidence = {
        "declarationId": row[0], "name": row[1], "typeText": row[3],
        "typeStatus": row[5], "authority": row[6], "path": row[10],
        "line": row[11], "freshness": args.freshness, "freshnessEvidence": freshness,
    }
    return analyze_difference(request, candidate_signature=str(row[3]), candidate_evidence=evidence)


def _freshness(args: Any, repo_root: Path, index_path: Path | None) -> dict[str, Any]:
    if args.freshness == "stored":
        return {"freshness": "stored"}
    return inspect_proof_search_index(repo_root, index_path=index_path, verify_sources=True)


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
            "Indexed type text does not establish Lean applicability unless a structurally rendered type is uniquely attributable.",
            "Use proof-search check or discover for explicit Lean candidate checking.",
        ],
    }


__all__ = ["candidate_match", "dispatch_explain", "unavailable"]
