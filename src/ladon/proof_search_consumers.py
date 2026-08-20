"""Bounded reverse declaration-consumer queries over semantic index evidence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from ladon.proof_search_coverage import evaluate_coverage


@dataclass(frozen=True)
class ConsumerRequest:
    target: str
    kind: str = "all"
    ownership: str = "all"
    limit: int = 100

    def __post_init__(self) -> None:
        if not self.target or self.kind not in {"all", "type", "value"} or self.ownership not in {"all", "project", "external"}:
            raise ValueError("invalid consumer query")
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("consumer limit must be between 1 and 1000")


def query_consumers(connection: sqlite3.Connection, request: ConsumerRequest) -> dict[str, Any]:
    """Resolve one target and fetch reverse users through the target index."""

    symbols = connection.execute("SELECT name,declaration_id,kind,ownership FROM symbols WHERE name = ?", (request.target,)).fetchall()
    if not symbols:
        return _result(request, [], [], [{"kind": "target", "subject": request.target, "reason": "target_missing"}], "unavailable")
    coverage = evaluate_coverage(connection, "declaration_dependencies", "declaration_dependencies")
    rows = connection.execute(_consumer_sql(request), _consumer_values(request)).fetchall()
    type_rows = [_consumer_row(row) for row in rows[:request.limit] if row[1] == "type"]
    value_rows = [_consumer_row(row) for row in rows[:request.limit] if row[1] == "value"]
    status = "complete"
    omissions: list[dict[str, str]] = []
    if coverage["status"] in {"not-populated", "partial", "integrity-unavailable"}:
        status = coverage["status"]
        omissions.append({"kind": "coverage", "subject": "declaration_dependencies", "reason": str(coverage["reason"] or coverage["status"])})
    return _result(request, type_rows, value_rows, omissions, status)


def _consumer_sql(request: ConsumerRequest) -> str:
    clauses = ["dd.target = ?"]
    if request.kind != "all":
        clauses.append("dd.kind = ?")
    if request.ownership != "all":
        clauses.append("s.ownership = ?")
    return (
        "SELECT dd.source,dd.kind,dd.authority,dd.status,d.name,d.module,d.path,d.line,s.ownership "
        "FROM declaration_dependencies AS dd JOIN symbols AS s ON s.name = dd.source "
        "LEFT JOIN declarations AS d ON d.id = s.declaration_id WHERE "
        + " AND ".join(clauses)
        + " ORDER BY d.module,d.line,dd.source LIMIT ?"
    )


def _consumer_values(request: ConsumerRequest) -> tuple[Any, ...]:
    values: list[Any] = [request.target]
    if request.kind != "all":
        values.append(request.kind)
    if request.ownership != "all":
        values.append(request.ownership)
    values.append(request.limit + 1)
    return tuple(values)


def _consumer_row(row: sqlite3.Row) -> dict[str, Any]:
    return {"source": row[0], "kind": row[1], "authority": row[2], "status": row[3], "name": row[4], "module": row[5], "path": row[6], "line": row[7], "ownership": row[8]}


def _result(request: ConsumerRequest, type_rows: list[dict[str, Any]], value_rows: list[dict[str, Any]], omissions: list[dict[str, str]], status: str) -> dict[str, Any]:
    return {"schema": "ladon-proof-consumers-result-v1", "schemaVersion": 2, "operation": "consumers", "status": status, "target": request.target, "results": {"type": type_rows, "value": value_rows}, "coverage": {"status": status, "typeReturned": len(type_rows), "valueReturned": len(value_rows), "authority": "sqlite_semantic_dependency_index"}, "omissions": omissions, "bounds": {"limit": request.limit}, "compatibility": {"v1": "same-shape-with-coverage-status", "deprecated": False}, "nonclaims": ["Consumer rows are bounded index evidence, not exhaustive proof-term use without complete semantic coverage."]}


__all__ = ["ConsumerRequest", "query_consumers"]
