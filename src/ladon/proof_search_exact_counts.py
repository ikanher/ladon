"""Exact-name population counts, separate from preregistered ranking inputs."""

from __future__ import annotations

import sqlite3
from typing import Any

from ladon.proof_search_name_query import is_exact_name_query
from ladon.proof_search_query import (
    _add_exclusions,
    _add_module_filter,
    _add_named_scope_filter,
    _DeclarationQuery,
    resolve_scope_modules,
)


def exact_name_counts(
    connection: sqlite3.Connection,
    *,
    text: str,
    scope: str,
    roots: tuple[str, ...],
    exclusions: tuple[str, ...],
) -> tuple[int, int]:
    """Count exact qualified and basename hits in the selected population."""

    if not is_exact_name_query(text):
        return 0, 0
    modules, _ = resolve_scope_modules(connection, scope, roots)
    if modules is not None and not modules:
        return 0, 0
    filters = _DeclarationQuery()
    _add_exclusions(filters, exclusions)
    _add_module_filter(filters, modules)
    _add_named_scope_filter(filters, scope, roots)
    where = f" AND {' AND '.join(filters.clauses)}" if filters.clauses else ""
    qualified = _count(connection, "d.candidate_name = ? COLLATE NOCASE", where,
                       (text, *filters.values))
    basename = _count(connection,
                      "d.name = ? COLLATE NOCASE AND d.candidate_name != ? COLLATE NOCASE",
                      where, (text, text, *filters.values))
    if text.isascii():
        return qualified, basename
    # SQLite NOCASE is ASCII-only. Unicode names use Python casefold over the
    # selected name population; this changes counting, not ranked retrieval.
    selected = connection.execute(
        "SELECT d.candidate_name,d.name FROM declarations AS d WHERE 1=1" + where,
        filters.values,
    )
    folded = text.casefold()
    qualified = 0
    basename = 0
    for candidate, name in selected:
        candidate_exact = str(candidate).casefold() == folded
        qualified += candidate_exact
        basename += str(name).casefold() == folded and not candidate_exact
    return qualified, basename


def _count(
    connection: sqlite3.Connection, condition: str, where: str, values: tuple[str, ...]
) -> int:
    return int(connection.execute(
        "SELECT COUNT(*) FROM declarations AS d WHERE " + condition + where, values,
    ).fetchone()[0])

def match_summary(
    rows: list[dict[str, Any]], text: str | None, qualified: int, basename: int
) -> dict[str, Any]:
    folded = text.casefold() if text else None
    exact_rows = [
        row for row in rows if folded is not None and (
            str(row.get("name", "")).casefold() == folded
            or str(row.get("candidateName", "")).casefold() == folded
        )
    ]
    return {
        "exactMatches": qualified + basename,
        "qualifiedExactMatches": qualified,
        "basenameExactMatches": basename,
        "exactCountScope": (
            "selected-indexed-population" if text and is_exact_name_query(text)
            else "not-applicable"
        ),
        "lexicalSuggestionsReturned": len(rows) - len(exact_rows),
    }
