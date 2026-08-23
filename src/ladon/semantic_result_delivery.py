"""Persist semantic evidence before emitting a compact transport projection.

Canonical semantic results remain the audit source.  Compact projections may
omit their ProofIR bodies only after this module has atomically registered the
complete artifact bundle and re-resolved every emitted environment and check
reference.  Registry state is operational cache state; it never upgrades the
authority recorded by the artifacts themselves.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.semantic_evidence_registry import (
    DEFAULT_MAX_DATABASE_BYTES,
    SemanticEvidenceRegistry,
    default_semantic_evidence_registry_path,
)
from ladon.semantic_result_projection import project_semantic_result


def deliver_semantic_result(
    payload: Mapping[str, Any],
    *,
    projection: str,
    repo_root: Path,
    registry_path: Path | None = None,
    max_registry_bytes: int = DEFAULT_MAX_DATABASE_BYTES,
) -> dict[str, Any]:
    """Return one audit or registry-closed compact semantic result.

    Audit output is a detached copy of the canonical result and performs no
    cache write.  ``llm`` and ``review`` output first commit every artifact in
    one registry transaction and then read each identity back before projecting.
    """

    if projection == "audit":
        return project_semantic_result(payload, projection="audit")
    artifacts = collect_semantic_artifacts(payload)
    registered: dict[str, Mapping[str, Any]] = {}
    if artifacts:
        path = registry_path or default_semantic_evidence_registry_path(repo_root)
        registry = SemanticEvidenceRegistry(path, max_database_bytes=max_registry_bytes)
        registration = registry.register_bundle(artifacts)
        artifact_refs = {
            str(artifact["artifactId"])
            for artifact in artifacts
            if isinstance(artifact.get("artifactId"), str)
        }
        registered = {
            artifact_ref: registry.resolve_artifact(artifact_ref)
            for artifact_ref in sorted(artifact_refs)
        }
        _verify_registration(registry, registration)
    return project_semantic_result(
        payload,
        projection=projection,
        registered_artifacts=registered,
    )


def collect_semantic_artifacts(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Collect the exact artifact bodies owned by one canonical semantic result."""

    rows: list[dict[str, Any]] = []
    _append_artifacts(rows, payload)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return rows
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        check = candidate.get("check")
        if not isinstance(check, Mapping):
            continue
        _append_artifacts(rows, check)
        scratch = check.get("scratch")
        if isinstance(scratch, Mapping):
            _append_artifacts(rows, scratch)
    return rows


def _append_artifacts(rows: list[dict[str, Any]], owner: Mapping[str, Any]) -> None:
    artifacts = owner.get("artifacts")
    if not isinstance(artifacts, Sequence) or isinstance(
        artifacts, (str, bytes, bytearray)
    ):
        return
    rows.extend(dict(artifact) for artifact in artifacts if isinstance(artifact, Mapping))


def _verify_registration(
    registry: SemanticEvidenceRegistry,
    registration: Mapping[str, Any],
) -> None:
    environments = registration.get("environmentRefs")
    if isinstance(environments, list):
        for environment_ref in environments:
            registry.resolve_environment(str(environment_ref))
    check_runs = registration.get("checkRunRefs")
    if isinstance(check_runs, list):
        for reference in check_runs:
            if isinstance(reference, Mapping):
                registry.resolve_typed_ref(reference)


__all__ = ["collect_semantic_artifacts", "deliver_semantic_result"]
