"""SQLite-first type-directed declaration shortlist contract."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.proof_search_fragment_query import fragment_evidence, fragment_rows
from ladon.proof_search_fragments import normalized_fragments
from ladon.proof_search_query import resolve_scope_modules


@dataclass(frozen=True)
class TypeSearchRequest:
    pattern: str | None = None
    module: str | None = None
    namespace: str | None = None
    package: str | None = None
    scope: str = "repository"
    roots: tuple[str, ...] = ()
    limit: int = 20
    diagnostic_limit: int = 0
    freshness: str = "stored"
    fragments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self._validate_match()
        if not 1 <= self.limit <= 1000:
            raise ValueError("type search limit must be between 1 and 1000")
        if type(self.diagnostic_limit) is not int or not 0 <= self.diagnostic_limit <= 1000:
            raise ValueError("type-text diagnostic limit must be an integer between 0 and 1000")
        _validate_type_scope(self.scope, self.module, self.namespace, self.roots)
        if self.freshness not in {"stored", "verify"}:
            raise ValueError("type-text freshness must be stored or verify")

    def _validate_match(self) -> None:
        if self.pattern is None:
            if not self.fragments:
                raise ValueError("provide a literal pattern or normalized fragments")
            if len(self.fragments) > 32 or any(len(item) > 4096 for item in self.fragments):
                raise ValueError("type-text accepts at most 32 fragments of at most 4096 characters each")
            object.__setattr__(self, "fragments", normalized_fragments(self.fragments))
        elif self.fragments or not self.pattern.strip():
            raise ValueError("a literal pattern must be nonempty and used without fragments")


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
    clauses, values, scope_evidence = _selection(connection, request)
    if request.fragments:
        rows = fragment_rows(connection, _COLUMNS, clauses, values, request)
    else:
        rows = _literal_rows(connection, clauses, values, request)
    verification = verifier(tuple(str(row[2]) for row in rows[: request.limit]), request.pattern or "") if verifier else {}
    if any(verification.values()):
        raise ValueError("type-text freshness verifier cannot supply candidate verification")
    payload = _shortlist_payload(connection, request, rows, scope_evidence)
    if request.fragments:
        _record_signature_omissions(connection, clauses, values, payload)
    return payload


def _record_signature_omissions(connection, clauses, values, payload):
    # A missing suffix may contain the entire search term, even on a zero-hit query.
    where = " AND ".join(["o.kind = 'declaration'", *clauses])
    counts = dict(connection.execute(
        f"""SELECT o.reason, count(*) FROM omissions o JOIN declarations d ON d.id = o.subject
            WHERE {where} AND o.reason IN ('lexical_signature_unavailable', 'lexical_type_truncated')
            GROUP BY o.reason""", values))
    payload["coverage"]["indexedTypeOmissions"] = counts
    if counts:
        payload["coverage"]["populationComplete"] = False
        payload["omissions"].extend({"kind": "indexed-type", "reason": key, "count": count}
                                    for key, count in counts.items())


def _shortlist_payload(connection, request, rows, scope_evidence):
    result_rows, diagnostics = _result_rows(rows, request)
    from ladon.idea_history import attach_declaration_history

    attach_declaration_history(connection, result_rows, id_key="declarationId")
    truncated = len(rows) > request.limit + request.diagnostic_limit
    omission_rows = _omissions(scope_evidence, truncated, len(rows), request)
    field_counts = _field_counts(result_rows)
    payload = {
        "schema": "ladon-proof-search-type-text-result-v2",
        "schemaVersion": 2,
        "operation": "search-type-text",
        "matchMode": "type-text-overlap",
        "matchingPolicy": "literal-substring-sqlite-ascii-lower",
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
    if request.fragments:
        payload.update(schema="ladon-proof-search-type-fragment-result-v1", schemaVersion=1,
                       matchMode="normalized-type-fragments", matchingPolicy="case-sensitive-lean-token-sequence-v1")
        del payload["query"]["pattern"]
        payload["query"]["fragments"] = list(request.fragments)
    return payload


def _result_rows(
    rows: Sequence[sqlite3.Row],
    request: TypeSearchRequest,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows = [_result_row(row, request) for row in rows[: request.limit]]
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


def _result_row(row: sqlite3.Row, request: TypeSearchRequest) -> dict[str, Any]:
    """Expose bounded type evidence without returning unbounded source text."""

    result = {
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
        "bucket": "text-overlap",
    }
    if request.fragments:
        result.update(fragment_evidence(row, request.fragments))
    else:
        literal = _sqlite_lower(request.pattern or "")
        result["fieldContributions"] = {
            field: literal in _sqlite_lower(str(result[field] or ""))
            for field in ("renderedType", "conclusionText", "typeText")
        }
    return result


def _sqlite_lower(value: str) -> str:
    """Mirror SQLite's built-in lower(), which folds ASCII letters only."""
    return value.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"))


_COLUMNS = (
    "d.id,d.name,d.candidate_name,d.namespace,d.module,d.package,d.path,d.line,d.type_status,"
    "d.type_text,d.type_text_bytes,d.type_text_truncated,d.rendered_type,d.conclusion_text"
)


def _literal_rows(connection, clauses, values, request):
    literal = """(instr(lower(COALESCE(d.rendered_type,'')), lower(?)) > 0
        OR instr(lower(COALESCE(d.conclusion_text,'')), lower(?)) > 0
        OR instr(lower(COALESCE(d.type_text,'')), lower(?)) > 0)"""
    where = " AND ".join([literal, *clauses])
    return connection.execute(
        f"SELECT {_COLUMNS} FROM declarations d WHERE {where} "
        "ORDER BY d.type_status DESC,d.candidate_name,d.module,d.line,d.id LIMIT ?",
        (request.pattern, request.pattern, request.pattern, *values, request.limit + request.diagnostic_limit + 1),
    ).fetchall()


def _selection(connection, request):
    clauses, values, scope_evidence = _scope_predicate(connection, request)
    filters = ((request.module, "d.module = ?"), (request.package, "d.package = ?"))
    for value, clause in filters:
        if value:
            clauses.append(clause)
            values.append(value)
    if request.namespace:
        clauses.append("(d.namespace = ? OR instr(d.namespace, ?) = 1)")
        values.extend((request.namespace, f"{request.namespace}."))
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
        clause, namespace_values = _namespace_population(roots)
        clauses.append(clause)
        values.extend(namespace_values)
    if request.scope == "file":
        placeholders = ",".join("?" for _ in roots)
        clauses.append(f"d.path IN ({placeholders})")
        values.extend(roots)
    evidence = {"kind": request.scope, "roots": list(roots), "omissions": omissions, "modules": len(modules) if modules is not None else None}
    return clauses, values, evidence


def _namespace_population(roots: tuple[str, ...]) -> tuple[str, list[str]]:
    clause = "(" + " OR ".join("(d.namespace = ? OR instr(d.namespace, ?) = 1)" for _ in roots) + ")"
    values = [value for root in roots for value in (root, f"{root}.")]
    return clause, values


def _scope_roots(request: TypeSearchRequest) -> tuple[str, ...]:
    if request.roots:
        return request.roots
    if request.scope == "module" and request.module:
        return (request.module,)
    if request.scope == "namespace" and request.namespace:
        return (request.namespace,)
    return ()


__all__ = ["TypeSearchRequest", "query_type_shortlist"]
