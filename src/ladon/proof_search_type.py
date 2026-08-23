"""SQLite-first type-directed declaration shortlist contract."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.proof_search_query import resolve_scope_modules


@dataclass(frozen=True)
class TypeSearchRequest:
    pattern: str
    module: str | None = None
    namespace: str | None = None
    package: str | None = None
    scope: str = "repository"
    roots: tuple[str, ...] = ()
    limit: int = 20
    diagnostic_limit: int = 0
    freshness: str = "stored"

    def __post_init__(self) -> None:
        if not self.pattern.strip() or self.limit < 1 or self.limit > 1000:
            raise ValueError("type search pattern and limit are required")
        _validate_type_scope(self.scope, self.module, self.namespace, self.roots)
        if self.freshness not in {"stored", "verify"}:
            raise ValueError("type-text freshness must be stored or verify")


def _validate_type_scope(
    scope: str, module: str | None, namespace: str | None, roots: tuple[str, ...]
) -> None:
    supported = {"repository", "project", "external", "module", "namespace", "file", "imports", "closure", "neighborhood"}
    if scope not in supported:
        raise ValueError("type-text search scope is not implemented")
    if scope == "module" and not (module or roots):
        raise ValueError("type-text module scope requires --module")
    if scope == "namespace" and not (namespace or roots):
        raise ValueError("type-text namespace scope requires --namespace")
    if scope in {"file", "imports", "closure", "neighborhood"} and not roots:
        raise ValueError(f"type-text {scope} scope requires --root")


def query_type_shortlist(connection: sqlite3.Connection, request: TypeSearchRequest, *, verifier: Callable[[Sequence[str], str], Mapping[str, Mapping[str, Any]]] | None = None) -> dict[str, Any]:
    """Return deterministic lexical candidates without claiming Lean verification."""

    if request.freshness == "verify" and verifier is None:
        raise ValueError("type-text freshness verification requires the index verifier")
    clauses, values, scope_evidence = _type_text_predicate(connection, request)
    where = " AND ".join(clauses)
    rows = connection.execute(
        "SELECT d.id,d.name,d.candidate_name,d.namespace,d.module,d.package,d.path,d.line,d.type_status,"
        "d.type_text,d.type_text_bytes,d.type_text_truncated,d.rendered_type,d.conclusion_text "
        f"FROM declarations AS d WHERE {where} ORDER BY d.type_status DESC,d.candidate_name,d.module,d.line,d.id LIMIT ?",
        (*values, request.limit + request.diagnostic_limit + 1),
    ).fetchall()
    verification = verifier(tuple(str(row[2]) for row in rows[: request.limit]), request.pattern) if verifier else {}
    result_rows, diagnostics = _result_rows(rows, request, verification)
    truncated = len(rows) > request.limit + request.diagnostic_limit
    omission_rows = _omissions(scope_evidence, truncated, len(rows), request)
    field_counts = _field_counts(result_rows)
    return {
        "schema": "ladon-proof-search-type-result-v1",
        "operation": "search-type",
        "matchMode": "type-text-overlap",
        "status": "available",
        "freshness": "verified-fresh" if request.freshness == "verify" else "stored",
        "results": result_rows,
        "matched": len(rows),
        "matchedExact": not truncated,
        "returned": len(result_rows),
        "diagnostics": diagnostics,
        "query": {"pattern": request.pattern, "scope": request.scope, "module": request.module, "namespace": request.namespace, "package": request.package, "freshness": request.freshness},
        "coverage": {
            "shortlistMatchedLowerBound": len(rows),
            "returned": len(result_rows),
            "diagnosticReturned": len(diagnostics),
            "cap": request.limit,
            "diagnosticCap": request.diagnostic_limit,
            "populationComplete": not truncated and not scope_evidence.get("omissions"),
            "rowEvidenceComplete": not any(
                item["typeTextTruncated"] for item in result_rows
            ),
            "authority": "sqlite_lexical_shortlist",
            "scope": scope_evidence,
            "fieldContributionCounts": field_counts,
        },
        "truncated": truncated,
        "omissions": omission_rows,
        "nonclaims": ["Shortlist rows are not Lean elaboration or proof verification."],
    }


def _result_rows(
    rows: Sequence[sqlite3.Row],
    request: TypeSearchRequest,
    verification: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows = [_result_row(row, request.pattern) for row in rows[: request.limit]]
    for item in result_rows:
        item.update(verification.get(str(item["candidateName"]), {}))
    diagnostics = [
        {"declarationId": row[0], "candidateName": row[2], "reason": "shortlist_not_verified"}
        for row in rows[request.limit : request.limit + request.diagnostic_limit]
    ]
    return result_rows, diagnostics


def _omissions(
    scope_evidence: Mapping[str, Any],
    truncated: bool,
    lower_bound: int,
    request: TypeSearchRequest,
) -> list[dict[str, Any]]:
    omissions = list(scope_evidence.get("omissions", ()))
    if truncated:
        omissions.append(
            {
                "kind": "result-cap",
                "reason": "additional lexical matches were omitted by the result and diagnostic caps",
                "lowerBound": lower_bound,
                "cap": request.limit,
                "diagnosticCap": request.diagnostic_limit,
            }
        )
    return omissions


def _field_counts(result_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        field: sum(bool(item["fieldContributions"][field]) for item in result_rows)
        for field in ("renderedType", "conclusionText", "typeText")
    }


def _result_row(row: sqlite3.Row, pattern: str) -> dict[str, Any]:
    """Expose bounded type evidence without returning unbounded source text."""

    field_contributions = {
        field: pattern.casefold() in str(value or "").casefold()
        for field, value in (
            ("renderedType", row[12]),
            ("conclusionText", row[13]),
            ("typeText", row[9]),
        )
    }
    return {
        "declarationId": row[0],
        "name": row[1],
        "candidateName": row[2],
        "namespace": row[3],
        "module": row[4],
        "package": row[5],
        "path": row[6],
        "line": row[7],
        "authority": "lexical_shortlist",
        "verification": "not_requested",
        "typeStatus": row[8],
        "typeText": row[9],
        "typeTextBytes": row[10],
        "typeTextTruncated": bool(row[11]),
        "renderedType": row[12],
        "conclusionText": row[13],
        "fieldContributions": field_contributions,
        "bucket": "text-overlap",
    }


def _type_text_predicate(
    connection: sqlite3.Connection, request: TypeSearchRequest
) -> tuple[list[str], list[Any], dict[str, Any]]:
    clauses = [
        """(instr(lower(COALESCE(d.rendered_type,'')), lower(?)) > 0
        OR instr(lower(COALESCE(d.conclusion_text,'')), lower(?)) > 0
        OR instr(lower(COALESCE(d.type_text,'')), lower(?)) > 0)"""
    ]
    values: list[Any] = [request.pattern, request.pattern, request.pattern]
    scope_clauses, scope_values, scope_evidence = _scope_predicate(connection, request)
    clauses.extend(scope_clauses)
    values.extend(scope_values)
    filters = ((request.module, "d.module = ?"), (request.package, "d.package = ?"))
    for value, clause in filters:
        if value:
            clauses.append(clause)
            values.append(value)
    if request.namespace:
        clauses.append("(d.namespace = ? OR d.namespace LIKE ?)")
        values.extend((request.namespace, f"{request.namespace}.%"))
    return clauses, values, scope_evidence


def _scope_predicate(
    connection: sqlite3.Connection, request: TypeSearchRequest
) -> tuple[list[str], list[Any], dict[str, Any]]:
    roots = _scope_roots(request)
    modules, omissions = resolve_scope_modules(connection, request.scope, roots)
    clauses: list[str] = []
    values: list[Any] = []
    if modules is not None:
        if modules:
            placeholders = ",".join("?" for _ in modules)
            clauses.append(f"d.module IN ({placeholders})")
            values.extend(sorted(modules))
        else:
            clauses.append("1 = 0")
    if request.scope == "namespace" and roots:
        clauses.append("(d.namespace = ? OR d.namespace LIKE ?)")
        values.extend((roots[0], f"{roots[0]}.%"))
    if request.scope == "file":
        placeholders = ",".join("?" for _ in roots)
        clauses.append(f"d.path IN ({placeholders})")
        values.extend(roots)
    evidence = {"kind": request.scope, "roots": list(roots), "omissions": omissions, "modules": len(modules) if modules is not None else None}
    return clauses, values, evidence


def _scope_roots(request: TypeSearchRequest) -> tuple[str, ...]:
    if request.roots:
        return request.roots
    if request.scope == "module" and request.module:
        return (request.module,)
    if request.scope == "namespace" and request.namespace:
        return (request.namespace,)
    return ()


__all__ = ["TypeSearchRequest", "query_type_shortlist"]
