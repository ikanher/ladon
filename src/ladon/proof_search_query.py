"""Private bounded query planning for the persistent proof-search index."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']*")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


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
    )
    return rows, truncated, len(modules) if modules is not None else None, omissions


def resolve_scope_modules(
    connection: sqlite3.Connection,
    scope: str,
    roots: tuple[str, ...],
) -> tuple[frozenset[str] | None, list[dict[str, str]]]:
    """Resolve one explicit scope to a finite module set where required."""

    if scope in {"repository", "project", "namespace", "file"}:
        return None, []
    if scope == "external":
        return frozenset(), [_external_omission()]
    if not roots:
        raise ValueError(f"scope {scope!r} requires at least one --root")
    known = _known_modules(connection)
    omissions = _missing_root_omissions(roots, known)
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
) -> tuple[list[dict[str, Any]], bool]:
    """Build and execute a parameterized bounded declaration query."""

    if modules is not None and not modules:
        return [], False
    query = _DeclarationQuery()
    _add_text_filter(query, text)
    _add_module_filter(query, modules)
    _add_named_scope_filter(query, scope, roots)
    query.values.append(limit + 1)
    rows = [dict(row) for row in connection.execute(_declaration_sql(query), query.values)]
    return [_query_row(row) for row in rows[:limit]], len(rows) > limit


def _add_text_filter(query: _DeclarationQuery, text: str | None) -> None:
    """Prefer the FTS surface and retain a symbol-only fallback."""

    if not text:
        return
    tokens = sorted(_semantic_tokens(text))
    if tokens:
        query.table += " JOIN declaration_search ON declaration_search.rowid = d.rowid"
        query.clauses.append("declaration_search MATCH ?")
        query.values.append(" AND ".join(f'"{token}"*' for token in tokens))
        return
    query.clauses.append(
        "(d.candidate_name LIKE ? ESCAPE '\\' OR d.name LIKE ? ESCAPE '\\' "
        "OR d.type_text LIKE ? ESCAPE '\\')"
    )
    pattern = f"%{_escape_like(text)}%"
    query.values.extend((pattern, pattern, pattern))


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
        clauses.append("(d.namespace = ? OR d.namespace LIKE ?)")
        query.values.extend((root, f"{_escape_like(root)}.%"))
    query.clauses.append("(" + " OR ".join(clauses) + ")")


def _add_file_filter(query: _DeclarationQuery, roots: tuple[str, ...]) -> None:
    if not roots:
        raise ValueError("file scope requires at least one --root")
    placeholders = ",".join("?" for _ in roots)
    query.clauses.append(f"d.path IN ({placeholders})")
    query.values.extend(roots)


def _declaration_sql(query: _DeclarationQuery) -> str:
    where = " WHERE " + " AND ".join(query.clauses) if query.clauses else ""
    return (
        "SELECT d.id, d.name, d.candidate_name, d.namespace, d.kind, d.module, "
        "d.package, d.path, d.line, d.column_number, d.type_text, "
        "d.type_text_bytes, d.type_text_truncated, d.type_status, d.authority, "
        "d.structure_name FROM "
        + query.table
        + where
        + " ORDER BY d.candidate_name IS NULL, d.candidate_name, d.module, d.line LIMIT ?"
    )


def _query_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Adapt private column names to the v1 result contract."""

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
                part.casefold()
                for part in _CAMEL_BOUNDARY_RE.split(underscored)
                if len(part) > 1
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


def _external_omission() -> dict[str, str]:
    return {
        "kind": "package",
        "subject": "external",
        "reason": "external_declarations_not_indexed_v1",
    }


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


__all__ = ["query_database", "resolve_scope_modules"]
