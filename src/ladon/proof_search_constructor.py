"""Bounded dependent-constructor field coverage and leakage evidence."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from ladon.proof_search_coverage import evaluate_coverage


@dataclass(frozen=True)
class ConstructorRequest:
    structure: str
    module: str | None = None
    arguments: tuple[str, ...] = ()
    limit: int = 100
    freshness: str = "stored"

    def __post_init__(self) -> None:
        if not self.structure or self.limit < 1:
            raise ValueError("structure and positive limit are required")
        if self.freshness not in {"stored", "verify"}:
            raise ValueError("freshness must be stored or verify")


def constructor_coverage(request: ConstructorRequest, fields: Iterable[Mapping[str, Any]], *, coverage_status: str | None = None) -> dict[str, Any]:
    available_fields = list(fields)
    rows = _field_rows(request, available_fields)
    status = "available" if available_fields or coverage_status == "complete" else "unavailable"
    omissions = [] if available_fields or coverage_status == "complete" else [{"kind": "structure_fields", "subject": request.structure, "reason": "fields_not_populated"}]
    return {"schema": "ladon-constructor-coverage-result-v1", "schemaVersion": 2, "operation": "constructor-coverage", "status": status, "structure": request.structure, "fields": rows, "summary": {"fieldCount": len(rows), "supplied": sum(row["classification"] == "supplied-in-scope" for row in rows), "residual": sum(row["classification"] == "residual-premise" for row in rows)}, "freshness": request.freshness, "coverage": {"status": coverage_status or ("complete" if available_fields else "structure-fields-not-indexed"), "authority": "bounded_constructor_analysis", "cap": request.limit}, "compatibility": {"v1": "same-shape-with-coverage-status", "deprecated": False}, "omissions": omissions, "nonclaims": ["Constructor coverage is bounded evidence, not a Lean proof certificate."]}


def _field_rows(request: ConstructorRequest, fields: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for field in fields[: request.limit]:
        name = str(field.get("name", ""))
        supplied = bool(field.get("supplied"))
        classification = "supplied-in-scope" if supplied else ("unavailable" if field.get("unavailable") else "residual-premise")
        rows.append({"field": name, "classification": classification, "type": field.get("type", ""), "residuals": [] if supplied else [str(field.get("type", ""))], "leakage": _leakage(field), "candidates": list(field.get("candidates", ())), "routeCard": {"structure": request.structure, "field": name, "authority": "bounded_constructor_analysis"}})
    return rows


def load_constructor_fields(connection: sqlite3.Connection, request: ConstructorRequest) -> tuple[list[dict[str, Any]], str]:
    """Load one exact structure and its ordered stored fields read-only."""
    clauses = ["name = ?"]
    values: list[Any] = [request.structure]
    if request.module:
        clauses.append("module = ?")
        values.append(request.module)
    structures = connection.execute(
        "SELECT declaration_id,name,module FROM structures WHERE " + " AND ".join(clauses) + " ORDER BY module,name",
        tuple(values),
    ).fetchall()
    if len(structures) != 1:
        return [], "unavailable"
    structure_id = str(structures[0][0])
    status = str(evaluate_coverage(connection, "structure_fields", "structure_fields")["status"])
    rows = connection.execute(
        "SELECT name,type_text,status FROM structure_fields WHERE structure_id=? ORDER BY ordinal LIMIT ?",
        (structure_id, request.limit + 1),
    ).fetchall()
    return [{"name": row[0], "type": row[1] or "", "unavailable": row[2] == "unavailable"} for row in rows], status


def _leakage(field: Mapping[str, Any]) -> dict[str, Any]:
    if field.get("equivalentInput"):
        return {"class": "equivalent_field_input", "evidence": field["equivalentInput"]}
    if field.get("projectionDependency"):
        return {"class": "direct_projection_dependency", "evidence": field["projectionDependency"]}
    if field.get("aliasProjection"):
        return {"class": "alias_projection_dependency", "evidence": field["aliasProjection"]}
    return {"class": "none", "evidence": None}


__all__ = ["ConstructorRequest", "constructor_coverage", "load_constructor_fields"]
