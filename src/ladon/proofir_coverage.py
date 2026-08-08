"""Open-world coverage and negative-evidence projections."""

from __future__ import annotations

import sqlite3
from typing import Any

EVIDENCE_FAMILIES = ("catalog", "surface", "claim", "attachment", "replay", "dag", "witness", "lineage")


def query_proofir_coverage(connection: sqlite3.Connection, *, theorem: str | None = None) -> dict[str, Any]:
    generation = connection.execute("SELECT generation_id,status,artifact_count FROM proofir_generations WHERE active=1").fetchone()
    configured = generation is not None and generation[1] == "configured"
    population = {"catalog": _count(connection, "proofir_artifacts"), "surface": _count(connection, "proofir_surfaces"), "claim": _count(connection, "proofir_claims"), "attachment": _count(connection, "proofir_attachments"), "replay": _count(connection, "proofir_replay_runs"), "dag": _count(connection, "proofir_dags"), "witness": _count(connection, "proofir_dag_witnesses"), "lineage": _count(connection, "lineage_closures")}
    sections = {}
    for family in EVIDENCE_FAMILIES:
        matched = population[family]
        state = "not-configured" if not configured else ("observed" if matched else "observed-absent")
        sections[family] = {"configuration": "configured" if configured else "not-configured", "availability": "available" if configured else "unavailable", "inspected": matched, "matched": matched, "state": state, "reason": _reason(family, matched, configured)}
    return {"schema": "ladon-proofir-coverage-v1", "generation": generation[0] if generation else None, "theorem": theorem, "families": sections, "nonclaims": ["Coverage is bounded by configured and inspected inputs; observed absence is not proof of mathematical or Lean-level nonexistence."]}


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _reason(family: str, matched: int, configured: bool) -> str:
    if not configured:
        return "no ProofIR manifest configured"
    return f"{family} population inspected" if matched else f"no {family} rows observed in active generation"


__all__ = ["EVIDENCE_FAMILIES", "query_proofir_coverage"]
