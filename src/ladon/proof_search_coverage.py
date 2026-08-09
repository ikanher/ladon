"""Read-only coverage evaluation shared by semantic query surfaces."""

from __future__ import annotations

import sqlite3
from typing import Any


def evaluate_coverage(connection: sqlite3.Connection, collection: str, table: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT status,authority,reason,observed,total_known FROM evidence_coverage WHERE collection=?",
        (collection,),
    ).fetchone()
    population = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    if row is None:
        return {"status": "unavailable", "authority": "unknown", "reason": "coverage_missing", "observed": population, "totalKnown": False}
    status = str(row[0])
    if status == "complete" and int(row[4]) != 1:
        status = "integrity-unavailable"
    return {"status": status, "authority": str(row[1]), "reason": row[2], "observed": population, "declaredObserved": int(row[3]), "totalKnown": bool(row[4])}


__all__ = ["evaluate_coverage"]
