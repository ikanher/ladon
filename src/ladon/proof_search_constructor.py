"""Bounded dependent-constructor field coverage and leakage evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


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


def constructor_coverage(request: ConstructorRequest, fields: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for field in list(fields)[: request.limit]:
        name = str(field.get("name", ""))
        supplied = bool(field.get("supplied"))
        leakage = _leakage(field)
        classification = "supplied-in-scope" if supplied else ("unavailable" if field.get("unavailable") else "residual-premise")
        rows.append({"field": name, "classification": classification, "type": field.get("type", ""), "residuals": [] if supplied else [str(field.get("type", ""))], "leakage": leakage, "candidates": list(field.get("candidates", ())), "routeCard": {"structure": request.structure, "field": name, "authority": "bounded_constructor_analysis"}})
    return {"schema": "ladon-constructor-coverage-result-v1", "operation": "constructor-coverage", "status": "available", "structure": request.structure, "fields": rows, "summary": {"fieldCount": len(rows), "supplied": sum(row["classification"] == "supplied-in-scope" for row in rows), "residual": sum(row["classification"] == "residual-premise" for row in rows)}, "freshness": request.freshness, "coverage": {"authority": "bounded_constructor_analysis", "cap": request.limit}, "omissions": [], "nonclaims": ["Constructor coverage is bounded evidence, not a Lean proof certificate."]}


def _leakage(field: Mapping[str, Any]) -> dict[str, Any]:
    if field.get("equivalentInput"):
        return {"class": "equivalent_field_input", "evidence": field["equivalentInput"]}
    if field.get("projectionDependency"):
        return {"class": "direct_projection_dependency", "evidence": field["projectionDependency"]}
    if field.get("aliasProjection"):
        return {"class": "alias_projection_dependency", "evidence": field["aliasProjection"]}
    return {"class": "none", "evidence": None}


__all__ = ["ConstructorRequest", "constructor_coverage"]
