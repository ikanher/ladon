"""Validated ProofIR v3 projection seam for the ordinary proof-search index."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from ladon.proofir_sqlite_v3 import project_envelopes, projection_counts
from ladon.proofir_v3 import validate_envelope


def project_v3_catalog(connection: sqlite3.Connection, snapshot: Any) -> int:
    """Atomically project the captured native-v3 catalog population.

    A catalog record describes bytes observed during snapshot capture.  Re-read
    those bytes only after checking the digest so a changed path cannot turn a
    catalog generation into a silently partial projection.
    """

    envelopes: list[dict[str, Any]] = []
    for artifact in snapshot.proofir_artifacts:
        if artifact.state != "cataloged" or artifact.schema_version != "3.0":
            continue
        try:
            raw = artifact.path.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"ProofIR artifact {artifact.relative_path} is unreadable after catalog capture"
            ) from exc
        if hashlib.sha256(raw).hexdigest() != artifact.sha256:
            raise ValueError(
                f"ProofIR artifact {artifact.relative_path} changed after catalog capture"
            )
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"ProofIR artifact {artifact.relative_path} is invalid after catalog capture"
            ) from exc
        envelopes.append(validate_envelope(value).to_dict())

    counts = project_envelopes(
        connection,
        envelopes,
        exact_inventory=False,
        manage_user_version=False,
    )
    return int(counts["artifacts"])


def catalog_projection_reconciliation(
    connection: sqlite3.Connection,
) -> dict[str, int | bool]:
    """Reconcile cataloged v3 candidates with semantic rows and rejections."""

    candidates, cataloged, rejected = connection.execute(
        "SELECT count(*),"
        "sum(CASE WHEN state='cataloged' THEN 1 ELSE 0 END),"
        "sum(CASE WHEN state!='cataloged' THEN 1 ELSE 0 END) "
        "FROM proofir_artifacts WHERE schema_version='3.0'"
    ).fetchone()
    projected = int(
        connection.execute("SELECT count(*) FROM proofir_v3_artifacts").fetchone()[0]
    )
    rejected_with_diagnostics = int(
        connection.execute(
            "SELECT count(DISTINCT a.artifact_id) "
            "FROM proofir_artifacts AS a "
            "JOIN proofir_diagnostics AS d ON d.artifact_id=a.artifact_id "
            "WHERE a.schema_version='3.0' AND a.state!='cataloged'"
        ).fetchone()[0]
    )
    omissions = int(
        connection.execute("SELECT count(*) FROM proofir_v3_omissions").fetchone()[0]
    )
    candidate_count = int(candidates or 0)
    cataloged_count = int(cataloged or 0)
    rejected_count = int(rejected or 0)
    normalized_rows = sum(projection_counts(connection).values())
    return {
        "canonicalCandidates": candidate_count,
        "cataloged": cataloged_count,
        "rejected": rejected_count,
        "rejectedWithDiagnostics": rejected_with_diagnostics,
        "projectedArtifacts": projected,
        "normalizedRows": normalized_rows,
        "omissions": omissions,
        "complete": (
            candidate_count == projected + rejected_count
            and projected == cataloged_count
            and rejected_with_diagnostics == rejected_count
        ),
    }


__all__ = ["catalog_projection_reconciliation", "project_v3_catalog"]
