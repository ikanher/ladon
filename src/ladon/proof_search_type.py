"""SQLite-first type-directed declaration shortlist contract."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TypeSearchRequest:
    pattern: str
    module: str | None = None
    namespace: str | None = None
    package: str | None = None
    scope: str = "repository"
    limit: int = 20
    diagnostic_limit: int = 0
    freshness: str = "stored"

    def __post_init__(self) -> None:
        if not self.pattern.strip() or self.limit < 1 or self.limit > 1000:
            raise ValueError("type search pattern and limit are required")
        if self.freshness not in {"stored", "verify"}:
            raise ValueError("freshness must be stored or verify")


def query_type_shortlist(connection: sqlite3.Connection, request: TypeSearchRequest, *, verifier: Callable[[Sequence[str], str], Mapping[str, Mapping[str, Any]]] | None = None) -> dict[str, Any]:
    """Return deterministic lexical candidates without claiming Lean verification."""

    clauses = ["(d.rendered_type LIKE ? OR d.conclusion_text LIKE ? OR d.type_text LIKE ?)"]
    pattern = f"%{request.pattern}%"
    values: list[Any] = [pattern, pattern, pattern]
    if request.module:
        clauses.append("d.module = ?")
        values.append(request.module)
    if request.namespace:
        clauses.append("(d.namespace = ? OR d.namespace LIKE ?)")
        values.extend((request.namespace, f"{request.namespace}.%"))
    if request.package:
        clauses.append("d.package = ?")
        values.append(request.package)
    where = " AND ".join(clauses)
    rows = connection.execute(
        "SELECT d.id,d.name,d.candidate_name,d.namespace,d.module,d.package,d.path,d.line,d.type_status "
        f"FROM declarations AS d WHERE {where} ORDER BY d.type_status DESC,d.candidate_name,d.module,d.line,d.id LIMIT ?",
        (*values, request.limit + request.diagnostic_limit + 1),
    ).fetchall()
    verification = verifier(tuple(str(row[2]) for row in rows[: request.limit]), request.pattern) if verifier else {}
    result_rows = [
        {"declarationId": row[0], "name": row[1], "candidateName": row[2], "namespace": row[3], "module": row[4], "package": row[5], "path": row[6], "line": row[7], "authority": "lexical_shortlist", "verification": "not_requested", "typeStatus": row[8], "bucket": "text-overlap"}
        for row in rows[: request.limit]
    ]
    for item in result_rows:
        item.update(verification.get(str(item["candidateName"]), {}))
    diagnostics = [
        {"declarationId": row[0], "candidateName": row[2], "reason": "shortlist_not_verified"}
        for row in rows[request.limit : request.limit + request.diagnostic_limit]
    ]
    return {
        "schema": "ladon-proof-search-type-result-v1",
        "operation": "search-type",
        "status": "available",
        "results": result_rows,
        "diagnostics": diagnostics,
        "query": {"pattern": request.pattern, "scope": request.scope, "module": request.module, "namespace": request.namespace, "package": request.package, "freshness": request.freshness},
        "coverage": {"shortlistMatched": len(rows), "returned": len(result_rows), "cap": request.limit, "authority": "sqlite_lexical_shortlist"},
        "truncated": len(rows) > request.limit + request.diagnostic_limit,
        "omissions": [],
        "nonclaims": ["Shortlist rows are not Lean elaboration or proof verification."],
    }


__all__ = ["TypeSearchRequest", "query_type_shortlist"]
