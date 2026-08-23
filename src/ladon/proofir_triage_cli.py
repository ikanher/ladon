"""Coverage-aware CLI projection for native ProofIR triage."""

from __future__ import annotations

from typing import Any

from ladon.proofir_v3_queries import query_v3_triage


def proofir_triage_payload(connection: Any, limit: int) -> dict[str, Any]:
    """Distinguish configuration, discovery, validation, and empty matches."""

    rows = query_v3_triage(connection, limit=limit + 1)
    truncated = len(rows) > limit
    rows = rows[:limit]
    generation = connection.execute(
        "SELECT generation_id,status,artifact_count,total_bytes "
        "FROM proofir_generations WHERE active=1 ORDER BY generation_id LIMIT 1"
    ).fetchone()
    discovered = int(generation[2]) if generation is not None else 0
    invalid = int(
        connection.execute(
            "SELECT COUNT(*) FROM proofir_artifacts WHERE state<>'cataloged'"
        ).fetchone()[0]
    )
    projected = _projected_v3_count(connection)
    configured = generation is not None and generation[1] == "configured"
    return {
        "schema": "ladon-proofir-v3-triage-v1",
        "status": "available",
        "reason": _empty_reason(configured, discovered, invalid, projected, rows),
        "generationIdentity": generation[0] if generation is not None else None,
        "freshness": "stored",
        "rows": rows,
        "matched": len(rows) if not truncated else len(rows) + 1,
        "matchedExact": not truncated,
        "returned": len(rows),
        "truncated": truncated,
        "coverage": {
            "configured": configured,
            "discoveredArtifacts": discovered,
            "invalidArtifacts": invalid,
            "projectedV3Artifacts": projected,
            "generationBytes": int(generation[3]) if generation is not None else 0,
        },
        "nonclaims": [
            "An empty triage population is not evidence that ProofIR was configured or validated."
        ],
    }


def _empty_reason(
    configured: bool,
    discovered: int,
    invalid: int,
    projected: int,
    rows: list[dict[str, Any]],
) -> str | None:
    if not configured:
        return "no-configured-artifacts"
    if discovered == 0:
        return "no-discovered-artifacts"
    if invalid and projected == 0:
        return "configured-artifacts-invalid"
    return "zero-triage-matches" if not rows else None


def _projected_v3_count(connection: Any) -> int:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='proofir_v3_artifacts'"
    ).fetchone()
    if exists is None:
        return 0
    return int(connection.execute("SELECT COUNT(*) FROM proofir_v3_artifacts").fetchone()[0])


__all__ = ["proofir_triage_payload"]
