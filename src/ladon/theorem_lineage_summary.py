"""Constant-shape aggregate summaries for stored theorem lineage closures."""

from __future__ import annotations

import sqlite3
import time
from typing import Any

from ladon.theorem_lineage_store import LineageIdentity, inspect_lineage_closure


def summarize_lineage(
    connection: sqlite3.Connection,
    identity: LineageIdentity,
    theorem: str,
) -> dict[str, Any]:
    """Return bounded closure metadata without recursive route enumeration."""

    started = time.monotonic()
    status = inspect_lineage_closure(connection, theorem, identity)
    if status["status"] != "fresh":
        return {
            "schema": "ladon-theorem-lineage-summary-result-v1",
            "operation": "lineage-summary",
            "status": "unavailable",
            "theorem": theorem,
            "reason": status.get("reason", status["status"]),
            "authority": "unavailable",
            "elapsedSeconds": round(time.monotonic() - started, 6),
            "nonclaim": _NONCLAIM,
        }
    closure_id = str(status["closureId"])
    nodes = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(project_owned),0), COALESCE(SUM(external_frontier),0), COALESCE(SUM(declared_axiom),0) FROM lineage_nodes WHERE closure_id=?",
        (closure_id,),
    ).fetchone()
    edges = connection.execute(
        "SELECT kind,COUNT(*) FROM lineage_edges WHERE closure_id=? GROUP BY kind ORDER BY kind",
        (closure_id,),
    ).fetchall()
    ownership = connection.execute(
        "SELECT project_owned,external_frontier,COUNT(*) FROM lineage_nodes WHERE closure_id=? GROUP BY project_owned,external_frontier ORDER BY project_owned,external_frontier",
        (closure_id,),
    ).fetchall()
    trust = connection.execute(
        "SELECT scope,COUNT(*) FROM lineage_trust WHERE closure_id=? GROUP BY scope ORDER BY scope",
        (closure_id,),
    ).fetchall()
    scc_count, omission_count = connection.execute(
        "SELECT (SELECT COUNT(DISTINCT component_id) FROM lineage_scc_members WHERE closure_id=?), "
        "(SELECT COUNT(*) FROM lineage_omissions WHERE closure_id=?)",
        (closure_id, closure_id),
    ).fetchone()
    page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
    page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
    metadata = {
        str(row[0]): str(row[1])
        for row in connection.execute(
            "SELECT key,value FROM metadata WHERE key IN ('maxIndexBytes','completeDatabaseMaxBytes','completeDatabaseBudgetPolicy')"
        ).fetchall()
    }
    return {
        "schema": "ladon-theorem-lineage-summary-result-v1",
        "operation": "lineage-summary",
        "status": "available",
        "theorem": theorem,
        "closureId": closure_id,
        "authority": "lean_environment",
        "freshness": "fresh",
        "nodes": {"total": int(nodes[0]), "projectOwned": int(nodes[1]), "externalFrontier": int(nodes[2]), "declaredAxioms": int(nodes[3])},
        "edges": {str(row[0]): int(row[1]) for row in edges},
        "ownership": [{"projectOwned": bool(row[0]), "externalFrontier": bool(row[1]), "count": int(row[2])} for row in ownership],
        "trust": {str(row[0]): int(row[1]) for row in trust},
        "sccCount": scc_count,
        "omissionCount": omission_count,
        "storage": {"pageSize": page_size, "pageCount": page_count, "allocatedBytes": page_size * page_count},
        "limits": {
            "baseBuildMaxBytes": _optional_int(metadata.get("maxIndexBytes")),
            "completeDatabaseMaxBytes": _optional_int(metadata.get("completeDatabaseMaxBytes")),
            "policy": metadata.get("completeDatabaseBudgetPolicy", "not-configured"),
        },
        "elapsedSeconds": round(time.monotonic() - started, 6),
        "nonclaim": _NONCLAIM,
    }


_NONCLAIM = "A closure summary reports stored dependencies and boundaries; it is not an alternative-proof enumeration or theorem replay."


def _optional_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


__all__ = ["summarize_lineage"]
