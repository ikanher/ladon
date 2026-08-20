"""Attributable, non-authoritative observations over manifest artifact links."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from ladon.proofir_v3 import canonical_bytes

LINK_POLICY_VERSION = "proofir-manifest-link-v2"
OBSERVER = {"name": "ladon-manifest-link-resolver", "version": LINK_POLICY_VERSION}


def manifest_link_observation(
    *,
    source_path: str,
    target_path: str,
    kind: str,
    declared_source_artifact_id: str | None,
    declared_target_artifact_id: str | None,
    resolved_source_artifact_id: str | None,
    resolved_target_artifact_id: str | None,
    resolved_source_file_digest: str | None = None,
    resolved_target_file_digest: str | None = None,
) -> dict[str, Any]:
    """Quote a repository-manifest relationship and diagnose its endpoints."""

    if not source_path or not target_path or not kind:
        raise ValueError("manifest link paths and kind must be non-empty")
    legacy = resolved_source_file_digest is None and resolved_target_file_digest is None
    endpoints = {
        "source": {
            "path": source_path,
            "declaredArtifactId": declared_source_artifact_id,
            "resolvedArtifactId": resolved_source_artifact_id,
        },
        "target": {
            "path": target_path,
            "declaredArtifactId": declared_target_artifact_id,
            "resolvedArtifactId": resolved_target_artifact_id,
        },
    }
    if not legacy:
        endpoints["source"]["resolvedFileDigest"] = resolved_source_file_digest
        endpoints["target"]["resolvedFileDigest"] = resolved_target_file_digest
    _validate_endpoint_ids(endpoints)
    diagnostics = _endpoint_diagnostics(endpoints)
    payload = {
        "observer": {
            "name": OBSERVER["name"],
            "version": "proofir-manifest-link-v1" if legacy else LINK_POLICY_VERSION,
        },
        "observationKind": "manifest-assertion",
        "linkKind": kind,
        "endpoints": endpoints,
        "linkResult": _link_result(diagnostics),
        "diagnostics": diagnostics,
        "semanticAcceptance": False,
        "limitations": [
            {
                "id": "manifest-link-is-not-semantic-authority",
                "message": "A manifest relationship does not establish proof semantics.",
            }
        ],
    }
    payload["observationId"] = "sha256:" + hashlib.sha256(
        canonical_bytes(payload)
    ).hexdigest()
    return payload


def insert_manifest_link_observations(
    connection: sqlite3.Connection,
    generation_id: str,
    relationships: tuple[tuple[str, str, str, str], ...],
    artifact_ids: dict[str, str],
    content_ids: dict[str, str | None],
    file_digests: dict[str, str] | None = None,
) -> int:
    """Persist configured paths as quoted, non-canonical link observations."""

    for source_path, target_path, kind, details_json in relationships:
        _insert_manifest_link(
            connection,
            generation_id,
            source_path,
            target_path,
            kind,
            details_json,
            artifact_ids,
            content_ids,
            file_digests,
        )
    return len(relationships)


def validate_manifest_link_observation(value: Any) -> dict[str, Any]:
    """Validate the persisted v2 link shape at the publication boundary.

    Older v1 observations used ``resolvedArtifactId`` as a file-level
    resolution.  They remain readable through the compatibility constructor,
    but publication never accepts that ambiguous shape.
    """

    if (
        not isinstance(value, dict)
        or value.get("observer", {}).get("version") != LINK_POLICY_VERSION
    ):
        raise ValueError("manifest link observation must use proofir-manifest-link-v2")
    endpoints = value.get("endpoints")
    if not isinstance(endpoints, dict) or set(endpoints) != {"source", "target"}:
        raise ValueError("manifest link observation endpoints are invalid")
    for endpoint in endpoints.values():
        _validate_v2_endpoint(endpoint)
    return value


def _validate_v2_endpoint(endpoint: Any) -> None:
    required = {"path", "declaredArtifactId", "resolvedArtifactId", "resolvedFileDigest"}
    if not isinstance(endpoint, dict) or set(endpoint) != required:
        raise ValueError("legacy manifest endpoint shape is not supported")
    if not endpoint["path"]:
        raise ValueError("manifest endpoint path must be non-empty")
    _validate_endpoint_ids({"endpoint": endpoint})
    if endpoint["resolvedFileDigest"] is not None and not _digest(endpoint["resolvedFileDigest"]):
        raise ValueError("resolvedFileDigest must be a sha256 file digest")


def _insert_manifest_link(
    connection,
    generation_id,
    source_path,
    target_path,
    kind,
    details_json,
    artifact_ids,
    content_ids,
    file_digests,
) -> None:
    source_id = artifact_ids.get(source_path)
    target_id = artifact_ids.get(target_path)
    if source_id is None or target_id is None:
        raise ValueError(
            f"ProofIR relationship references uncataloged artifact: "
            f"{source_path} -> {target_path}"
        )
    observation = manifest_link_observation(
        source_path=source_path,
        target_path=target_path,
        kind=kind,
        declared_source_artifact_id=None,
        declared_target_artifact_id=None,
            resolved_source_artifact_id=content_ids.get(source_path),
            resolved_target_artifact_id=content_ids.get(target_path),
            resolved_source_file_digest=(file_digests or {}).get(source_path),
            resolved_target_file_digest=(file_digests or {}).get(target_path),
    )
    validate_manifest_link_observation(observation)
    details = {
        "manifestDetails": json.loads(details_json),
        "linkObservation": observation,
    }
    connection.execute(
        "INSERT INTO proofir_relations(relation_id,generation_id,source_artifact_id,"
        "target_artifact_id,kind,details_json) VALUES(?,?,?,?,?,?)",
        (
            _relation_id(generation_id, source_id, target_id, kind),
            generation_id,
            source_id,
            target_id,
            kind,
            json.dumps(details, sort_keys=True, separators=(",", ":")),
        ),
    )


def _relation_id(generation_id: str, source_id: str, target_id: str, kind: str) -> str:
    value = {
        "generation": generation_id,
        "source": source_id,
        "target": target_id,
        "kind": kind,
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_endpoint_ids(endpoints: dict[str, dict[str, str | None]]) -> None:
    for endpoint in endpoints.values():
        for field in ("declaredArtifactId", "resolvedArtifactId"):
            value = endpoint[field]
            if value is not None and not _digest(value):
                raise ValueError(f"{field} must be a sha256 content ID")


def _endpoint_diagnostics(
    endpoints: dict[str, dict[str, str | None]],
) -> list[str]:
    diagnostics = []
    for side in ("source", "target"):
        endpoint = endpoints[side]
        declared = endpoint["declaredArtifactId"]
        resolved = endpoint["resolvedArtifactId"]
        if declared is None or resolved is None:
            diagnostics.append(f"missing-{side}-endpoint")
        elif declared != resolved:
            diagnostics.append(f"{side}-content-id-drift")
    return diagnostics


def _link_result(diagnostics: list[str]) -> str:
    if any(diagnostic.endswith("content-id-drift") for diagnostic in diagnostics):
        return "drifted"
    if diagnostics:
        return "unbound"
    return "bound-observation"


def _digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


__all__ = [
    "LINK_POLICY_VERSION",
    "insert_manifest_link_observations",
    "manifest_link_observation",
    "validate_manifest_link_observation",
]
