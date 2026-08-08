"""SQLite persistence for admitted ProofIR surfaces and replay provenance."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from ladon.proofir_catalog import CatalogArtifact
from ladon.proofir_input import (
    EXPECTED_INDEX_KIND,
    SURFACE_BUNDLE_KIND,
    normalize_proofir_index,
)


REPLAY_KIND = "proof_ir_lean_replay_provenance"
MAX_METADATA_BYTES = 16 * 1024


def insert_surface_and_replay_evidence(
    connection: sqlite3.Connection,
    generation_id: str,
    artifacts: tuple[CatalogArtifact, ...],
    artifact_ids: Mapping[str, str],
) -> dict[str, int]:
    """Insert all admitted surface/claim/replay rows for one generation."""

    counts = {"surfaces": 0, "claims": 0, "surfaceClaims": 0, "replayRuns": 0, "replaySurfaces": 0}
    payloads: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if artifact.state != "cataloged":
            continue
        payload = _read_payload(artifact)
        if payload is None:
            continue
        if artifact.artifact_kind in {EXPECTED_INDEX_KIND, SURFACE_BUNDLE_KIND}:
            inserted = _insert_surface_index(
                connection, artifact_ids[artifact.relative_path], payload
            )
            for key, value in inserted.items():
                counts[key] += value
            payloads[artifact.relative_path] = payload
    for artifact in artifacts:
        if artifact.state != "cataloged" or artifact.artifact_kind != REPLAY_KIND:
            continue
        payload = _read_payload(artifact)
        if payload is None:
            continue
        inserted = _insert_replay(
            connection,
            artifact,
            artifact_ids[artifact.relative_path],
            artifacts,
            artifact_ids,
            payloads,
            payload,
        )
        for key, value in inserted.items():
            counts[key] += value
    return counts


def _read_payload(artifact: CatalogArtifact) -> dict[str, Any] | None:
    raw = artifact.path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != artifact.sha256:
        raise ValueError(f"ProofIR artifact changed while building index: {artifact.relative_path}")
    payload = json.loads(raw.decode("utf-8"))
    return payload if isinstance(payload, dict) else None


def _insert_surface_index(
    connection: sqlite3.Connection,
    artifact_id: str,
    payload: dict[str, Any],
) -> dict[str, int]:
    normalized = normalize_proofir_index(payload)
    if normalized is None:
        return {"surfaces": 0, "claims": 0, "surfaceClaims": 0, "replayRuns": 0, "replaySurfaces": 0}
    counts = {"surfaces": 0, "claims": 0, "surfaceClaims": 0, "replayRuns": 0, "replaySurfaces": 0}
    surface_rows: dict[str, str] = {}
    for raw_surface in normalized.get("surfaces", []):
        if not isinstance(raw_surface, dict):
            continue
        surface_id = str(raw_surface.get("surfaceId", ""))
        if not surface_id:
            continue
        row_id = _id("surface", artifact_id, surface_id)
        surface_rows[surface_id] = row_id
        connection.execute(
            """
            INSERT INTO proofir_surfaces(
                surface_row_id, artifact_id, surface_id, claim_id,
                declaration_name, source_path, source_range_json, content_hash,
                status, authority_json, proof_trust, replay_boundary_json,
                extractor_guarantee, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_id,
                artifact_id,
                surface_id,
                str(raw_surface.get("claimId", "")) or None,
                str(raw_surface.get("declarationName", "")),
                str(raw_surface.get("sourcePath", "")),
                _json(raw_surface.get("sourceRange", {})),
                str(raw_surface.get("contentHash", "")) or None,
                str(raw_surface.get("status", "")),
                _json(raw_surface.get("authority", [])),
                str(raw_surface.get("proofTrust", "")),
                _json(raw_surface.get("replayBoundary", {})),
                str(raw_surface.get("extractorGuarantee", "")),
                _metadata(raw_surface),
            ),
        )
        counts["surfaces"] += 1
    for raw_claim in normalized.get("claims", []):
        if not isinstance(raw_claim, dict):
            continue
        claim_id = str(raw_claim.get("claimId", ""))
        if not claim_id:
            continue
        claim_row_id = _id("claim", artifact_id, claim_id)
        connection.execute(
            """
            INSERT INTO proofir_claims(
                claim_row_id, artifact_id, claim_id, status, authority_json,
                scope, proof_trust, replay_boundary_json, extractor_guarantee,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_row_id,
                artifact_id,
                claim_id,
                str(raw_claim.get("status", "")),
                _json(raw_claim.get("authority", [])),
                str(raw_claim.get("scope", "")),
                str(raw_claim.get("proofTrust", "")),
                _json(raw_claim.get("replayBoundary", {})),
                str(raw_claim.get("extractorGuarantee", "")),
                _metadata(raw_claim),
            ),
        )
        counts["claims"] += 1
        for surface_ref in _surface_refs(raw_claim):
            surface_id = surface_ref if isinstance(surface_ref, str) else str(surface_ref.get("surfaceId", ""))
            surface_row_id = surface_rows.get(surface_id)
            if surface_row_id is None:
                continue
            connection.execute(
                "INSERT INTO proofir_surface_claims(artifact_id, surface_row_id, claim_row_id) VALUES (?, ?, ?)",
                (artifact_id, surface_row_id, claim_row_id),
            )
            counts["surfaceClaims"] += 1
    return counts


def _insert_replay(
    connection: sqlite3.Connection,
    artifact: CatalogArtifact,
    artifact_id: str,
    artifacts: tuple[CatalogArtifact, ...],
    artifact_ids: Mapping[str, str],
    payloads: Mapping[str, dict[str, Any]],
    payload: dict[str, Any],
) -> dict[str, int]:
    provenance_id = str(payload.get("provenanceId", artifact.relative_path))
    replay_id = _id("replay", artifact_id, provenance_id)
    connection.execute(
        """
        INSERT INTO proofir_replay_runs(
            replay_id, artifact_id, provenance_id, module, command_json,
            return_code, repository_json, source_json, guarantee,
            authority_json, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            replay_id,
            artifact_id,
            provenance_id,
            str(payload.get("module", "")),
            _json(payload.get("command", [])),
            _integer(payload.get("returncode", -1), default=-1),
            _json(payload.get("repository", {})),
            _json(payload.get("source", {})),
            str(payload.get("guarantee", "")),
            _json(payload.get("authorityInterpretation", {})),
            _metadata(payload),
        ),
    )
    counts = {"surfaces": 0, "claims": 0, "surfaceClaims": 0, "replayRuns": 1, "replaySurfaces": 0}
    bundle = payload.get("surfaceBundle")
    if not isinstance(bundle, dict):
        return counts
    bundle_path = str(bundle.get("path", ""))
    bundle_hash = str(bundle.get("contentHash", ""))
    bundle_artifact = next(
        (
            candidate
            for candidate in artifacts
            if candidate.relative_path == bundle_path
            and candidate.artifact_kind == SURFACE_BUNDLE_KIND
        ),
        None,
    )
    if bundle_artifact is None:
        return counts
    bundle_id = artifact_ids[bundle_artifact.relative_path]
    exact = bundle_artifact.sha256 == bundle_hash.removeprefix("sha256:")
    bundle_payload = payloads.get(bundle_artifact.relative_path)
    known_surfaces = {
        str(row.get("surfaceId", ""))
        for row in (bundle_payload or {}).get("surfaces", [])
        if isinstance(row, dict)
    }
    if exact:
        relation_id = _id("relation", artifact_id, bundle_id, "replays")
        connection.execute(
            "INSERT OR IGNORE INTO proofir_relations(relation_id, generation_id, source_artifact_id, target_artifact_id, kind, details_json) VALUES (?, ?, ?, ?, ?, ?)",
            (relation_id, str(_generation(connection)), artifact_id, bundle_id, "replays", _json({"provenanceId": provenance_id})),
        )
    for surface_id in _replay_surface_ids(payload):
        status = "related" if exact and surface_id in known_surfaces else ("stale" if not exact else "foreign")
        connection.execute(
            "INSERT INTO proofir_replay_surfaces(replay_id, bundle_artifact_id, surface_id, status, diagnostic) VALUES (?, ?, ?, ?, ?)",
            (replay_id, bundle_id, surface_id, status, None if status == "related" else status),
        )
        counts["replaySurfaces"] += 1
    return counts


def _generation(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT generation_id FROM proofir_generations WHERE active = 1").fetchone()
    if row is None:
        raise ValueError("ProofIR generation is not active")
    return str(row[0])


def _replay_surface_ids(payload: dict[str, Any]) -> tuple[str, ...]:
    rows = payload.get("surfaces", [])
    return tuple(
        str(row.get("surfaceId", ""))
        for row in rows
        if isinstance(row, dict) and row.get("surfaceId")
    )


def _surface_refs(claim: dict[str, Any]) -> tuple[Any, ...]:
    refs: list[Any] = []
    for key in ("primaryTheoremSurfaces", "supportingTheoremSurfaces", "backgroundTheoremSurfaces"):
        value = claim.get(key, [])
        if isinstance(value, list):
            refs.extend(value)
    return tuple(refs)


def _metadata(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    encoded = payload.encode("utf-8")
    if len(encoded) <= MAX_METADATA_BYTES:
        return payload
    return json.dumps(
        {"truncated": True, "sha256": hashlib.sha256(encoded).hexdigest()},
        sort_keys=True,
        separators=(",", ":"),
    )


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _integer(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


__all__ = ["insert_surface_and_replay_evidence"]
