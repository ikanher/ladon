"""Private bounded query planning for the persistent proof-search index."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ladon.proof_search_name_query import (
    is_exact_name_query,
    name_casefold,
    semantic_name_segments_v1,
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']*")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_GENERIC_TERMS = frozenset({"bound", "path", "le", "eq", "of", "has", "map", "mem"})


@dataclass
class _DeclarationQuery:
    """Mutable SQL assembly state kept local to one bounded query."""

    table: str = "declarations AS d"
    clauses: list[str] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)


def query_database(
    connection: sqlite3.Connection,
    *,
    text: str | None,
    scope: str,
    roots: tuple[str, ...],
    limit: int,
    query_mode: str = "all",
    exclusions: tuple[str, ...] = (),
    min_matched_segments: int = 1,
) -> tuple[list[dict[str, Any]], bool, int | None, list[dict[str, str]]]:
    """Resolve scope and run one deterministic declaration query."""

    modules, omissions = resolve_scope_modules(connection, scope, roots)
    rows, truncated = _query_declarations(
        connection,
        text=text,
        modules=modules,
        scope=scope,
        roots=roots,
        limit=limit,
        query_mode=query_mode,
        exclusions=exclusions,
        min_matched_segments=min_matched_segments,
    )
    return rows, truncated, len(modules) if modules is not None else None, omissions


def resolve_scope_modules(
    connection: sqlite3.Connection,
    scope: str,
    roots: tuple[str, ...],
) -> tuple[frozenset[str] | None, list[dict[str, str]]]:
    """Resolve one explicit scope to a finite module set where required."""

    if scope in {"repository", "project", "namespace"}:
        return None, []
    if scope == "external":
        return frozenset(), [_external_omission()]
    if not roots:
        raise ValueError(f"scope {scope!r} requires at least one --root")
    known = _known_modules(connection)
    omissions = (
        _missing_file_omissions(roots, _known_module_paths(connection))
        if scope == "file"
        else _missing_root_omissions(roots, known)
    )
    if scope == "file":
        return None, omissions
    selected_roots = frozenset(set(roots) & known)
    return _expanded_modules(connection, scope, selected_roots), omissions


def _expanded_modules(
    connection: sqlite3.Connection,
    scope: str,
    roots: frozenset[str],
) -> frozenset[str]:
    """Expand module roots according to one graph-local scope."""

    if scope == "module":
        return roots
    imports = _module_edges(connection)
    if scope == "imports":
        return _direct_import_modules(roots, imports)
    if scope == "closure":
        return _transitive_modules(roots, imports)
    if scope == "neighborhood":
        return _neighborhood_modules(roots, imports)
    raise ValueError(f"scope {scope!r} has no module expansion")


def _query_declarations(
    connection: sqlite3.Connection,
    *,
    text: str | None,
    modules: frozenset[str] | None,
    scope: str,
    roots: tuple[str, ...],
    limit: int,
    query_mode: str,
    exclusions: tuple[str, ...],
    min_matched_segments: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Build and execute a parameterized bounded declaration query."""

    if modules is not None and not modules:
        return [], False
    query = _DeclarationQuery()
    _add_text_filter(query, text, query_mode=query_mode)
    _add_exclusions(query, exclusions)
    _add_module_filter(query, modules)
    _add_named_scope_filter(query, scope, roots)
    exact_key = name_casefold(text) if text and is_exact_name_query(text) else None
    if exact_key is not None:
        query.values.append(exact_key)
    query.values.append(limit + 1)
    rows = [
        dict(row)
        for row in connection.execute(
            _declaration_sql(query, prioritize_exact=exact_key is not None),
            query.values,
        )
    ]
    ranked = _rank_rows(rows, text, min_matched_segments)
    return [_query_row(row) for row in ranked[:limit]], len(ranked) > limit


def _rank_rows(rows: list[dict[str, Any]], text: str | None, minimum: int) -> list[dict[str, Any]]:
    if not text:
        return rows
    terms = tuple(sorted(_semantic_tokens(semantic_name_segments_v1(text))))
    ranked = []
    for row in rows:
        score_data = _row_score(row, terms, text)
        matched = score_data["matched"]
        if len(matched) < minimum and score_data["contribution"] != "exact":
            continue
        row["_rank"] = score_data
        ranked.append(row)
    ranked.sort(
        key=lambda row: (
            -row["_rank"]["score"],
            str(row.get("candidate_name") or ""),
            str(row.get("name") or ""),
            str(row.get("module") or ""),
            int(row.get("line") or 0),
        )
    )
    return ranked


def _row_score(row: Mapping[str, Any], terms: tuple[str, ...], text: str) -> dict[str, Any]:
    name = str(row.get("name", "")).casefold()
    candidate = str(row.get("candidate_name", "")).casefold()
    matched = [term for term in terms if term in name or term in candidate]
    specific = [term for term in matched if term not in _GENERIC_TERMS]
    folded = name_casefold(text)
    exact = int(name == folded or candidate == folded)
    score = exact * 10000 + len(specific) * 100 + len(matched) * 10 + int(bool(candidate))
    return {
        "score": score,
        "matchedSegments": sorted(set(matched)),
        "specificSegments": sorted(set(specific)),
        "contribution": "exact" if exact else ("specific" if specific else "generic"),
        "matched": matched,
        "specific": specific,
    }


def _add_text_filter(
    query: _DeclarationQuery,
    text: str | None,
    *,
    query_mode: str,
) -> None:
    """Prefer the FTS surface and retain a symbol-only fallback."""

    if not text:
        return
    if query_mode not in {"all", "any", "phrase"}:
        raise ValueError("query mode must be all, any, or phrase")
    tokens = sorted(_semantic_tokens(semantic_name_segments_v1(text)))
    if tokens:
        operator = " OR " if query_mode == "any" else " AND "
        expression = (
            f'"{semantic_name_segments_v1(text)}"'
            if query_mode == "phrase"
            else operator.join(f'"{token}"*' for token in tokens)
        )
        exact_clause = "d.name_casefold = ?" if is_exact_name_query(text) else "0"
        query.clauses.append(
            "(" + exact_clause + " OR d.rowid IN ("
            "SELECT rowid FROM declaration_search WHERE declaration_search MATCH ?))"
        )
        if is_exact_name_query(text):
            query.values.append(name_casefold(text))
        query.values.append(expression)
        return
    _add_fallback_text_filter(query, text)


def _add_fallback_text_filter(query: _DeclarationQuery, text: str) -> None:
    """Retain exact folded names when the ASCII-oriented FTS has no tokens."""

    exact = is_exact_name_query(text)
    exact_clause = "d.name_casefold = ? OR " if exact else ""
    query.clauses.append(
        "(" + exact_clause + "d.candidate_name LIKE ? ESCAPE '\\' OR d.name LIKE ? ESCAPE '\\' "
        "OR d.type_text LIKE ? ESCAPE '\\')"
    )
    pattern = f"%{_escape_like(text)}%"
    if exact:
        query.values.append(name_casefold(text))
    query.values.extend((pattern, pattern, pattern))


def _add_exclusions(query: _DeclarationQuery, exclusions: tuple[str, ...]) -> None:
    """Apply explicit folded-name exclusions before ranking."""

    for exclusion in exclusions:
        query.clauses.append("d.name_casefold NOT LIKE ? ESCAPE '\\'")
        query.values.append(f"%{_escape_like(name_casefold(exclusion))}%")


def _add_module_filter(
    query: _DeclarationQuery,
    modules: frozenset[str] | None,
) -> None:
    if modules is None:
        return
    placeholders = ",".join("?" for _ in modules)
    query.clauses.append(f"d.module IN ({placeholders})")
    query.values.extend(sorted(modules))


def _add_named_scope_filter(
    query: _DeclarationQuery,
    scope: str,
    roots: tuple[str, ...],
) -> None:
    if scope == "namespace":
        _add_namespace_filter(query, roots)
    elif scope == "file":
        _add_file_filter(query, roots)


def _add_namespace_filter(query: _DeclarationQuery, roots: tuple[str, ...]) -> None:
    if not roots:
        raise ValueError("namespace scope requires at least one --root")
    clauses = []
    for root in roots:
        clauses.append("(d.namespace = ? OR instr(d.namespace, ?) = 1)")
        query.values.extend((root, f"{root}."))
    query.clauses.append("(" + " OR ".join(clauses) + ")")


def _add_file_filter(query: _DeclarationQuery, roots: tuple[str, ...]) -> None:
    if not roots:
        raise ValueError("file scope requires at least one --root")
    placeholders = ",".join("?" for _ in roots)
    query.clauses.append(f"d.path IN ({placeholders})")
    query.values.extend(roots)


def _declaration_sql(query: _DeclarationQuery, *, prioritize_exact: bool = False) -> str:
    where = " WHERE " + " AND ".join(query.clauses) if query.clauses else ""
    exact_order = "(d.name_casefold = ?) DESC, " if prioritize_exact else ""
    return (
        "SELECT d.id, d.name, d.candidate_name, d.namespace, d.kind, d.module, "
        "d.package, d.path, d.line, d.column_number, d.type_text, "
        "d.type_text_bytes, d.type_text_truncated, d.type_status, d.authority, "
        "d.structure_name FROM "
        + query.table
        + where
        + " ORDER BY "
        + exact_order
        + "d.candidate_name IS NULL, d.candidate_name, d.module, d.line LIMIT ?"
    )


def _query_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Adapt private column names to the v1 result contract."""

    ranking = row.get("_rank")
    if isinstance(ranking, dict):
        ranking = {
            key: ranking[key]
            for key in ("score", "matchedSegments", "specificSegments", "contribution")
        }
    return {
        "id": row["id"],
        "name": row["name"],
        "candidateName": row["candidate_name"],
        "namespace": row["namespace"],
        "kind": row["kind"],
        "module": row["module"],
        "package": row["package"],
        "path": row["path"],
        "line": row["line"],
        "column": row["column_number"],
        "typeText": row["type_text"],
        "typeTextBytes": row["type_text_bytes"],
        "typeTextTruncated": bool(row["type_text_truncated"]),
        "typeStatus": row["type_status"],
        "authority": row["authority"],
        "structureName": row["structure_name"],
        "ranking": ranking,
    }


def _direct_import_modules(
    roots: Iterable[str],
    edges: Mapping[str, Iterable[str]],
) -> frozenset[str]:
    selected = set(roots)
    for root in tuple(selected):
        selected.update(edges.get(root, ()))
    return frozenset(selected)


def _neighborhood_modules(
    roots: Iterable[str],
    edges: Mapping[str, Iterable[str]],
) -> frozenset[str]:
    selected = set(roots)
    reverse = _reverse_edges(edges)
    for root in tuple(selected):
        selected.update(edges.get(root, ()))
        selected.update(reverse.get(root, ()))
    return frozenset(selected)


def _transitive_modules(
    roots: Iterable[str],
    edges: Mapping[str, Iterable[str]],
) -> frozenset[str]:
    selected = set(roots)
    pending = list(selected)
    while pending:
        source = pending.pop()
        for target in edges.get(source, ()):
            if target not in selected:
                selected.add(target)
                pending.append(target)
    return frozenset(selected)


def _known_modules(connection: sqlite3.Connection) -> frozenset[str]:
    return frozenset(str(row[0]) for row in connection.execute("SELECT name FROM modules"))


def _known_module_paths(connection: sqlite3.Connection) -> frozenset[str]:
    return frozenset(
        str(row[0])
        for row in connection.execute(
            "SELECT m.path FROM modules AS m "
            "LEFT JOIN declarations AS d ON d.path = m.path "
            "GROUP BY m.path HAVING COUNT(d.id) > 0"
        )
    )


def _module_edges(connection: sqlite3.Connection) -> dict[str, frozenset[str]]:
    edges: dict[str, set[str]] = {}
    for source, target in connection.execute("SELECT source, target FROM module_imports"):
        edges.setdefault(str(source), set()).add(str(target))
    return {source: frozenset(targets) for source, targets in edges.items()}


def _reverse_edges(
    edges: Mapping[str, Iterable[str]],
) -> dict[str, frozenset[str]]:
    reverse: dict[str, set[str]] = {}
    for source, targets in edges.items():
        for target in targets:
            reverse.setdefault(target, set()).add(source)
    return {target: frozenset(sources) for target, sources in reverse.items()}


def _semantic_tokens(value: str) -> frozenset[str]:
    """Segment qualified, underscored, and camel-case query text."""

    tokens: set[str] = set()
    for raw in _TOKEN_RE.findall(value.replace(".", " ")):
        for underscored in raw.split("_"):
            tokens.update(
                part.casefold() for part in _CAMEL_BOUNDARY_RE.split(underscored) if len(part) > 1
            )
    return frozenset(tokens)


def _missing_root_omissions(
    roots: Iterable[str],
    known: frozenset[str],
) -> list[dict[str, str]]:
    return [
        {"kind": "module", "subject": name, "reason": "root_not_indexed"}
        for name in sorted(set(roots) - known)
    ]


def _missing_file_omissions(
    roots: Iterable[str],
    known: frozenset[str],
) -> list[dict[str, str]]:
    return [
        {"kind": "file", "subject": name, "reason": "source_not_indexed"}
        for name in sorted(set(roots) - known)
    ]


def _external_omission() -> dict[str, str]:
    return {
        "kind": "package",
        "subject": "external",
        "reason": "external_declarations_not_indexed_v1",
    }


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


__all__ = ["query_database", "resolve_scope_modules"]
