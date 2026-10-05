"""Batch-budget and duplicate-ID preflight for native ProofIR envelopes."""

from __future__ import annotations

from typing import Any


def resolve_limits(
    legacy: int | None, artifact: int, batch: int, count: int
) -> tuple[int, int]:
    from ladon.proofir_v3 import _fail

    if legacy is not None:
        artifact = batch = legacy
    for name, bound in (
        ("max_artifact_bytes", artifact),
        ("max_batch_bytes", batch),
        ("max_artifacts", count),
    ):
        if not isinstance(bound, int) or isinstance(bound, bool) or bound <= 0:
            _fail("reference-valid", "invalid-bound", "", f"{name} must be positive")
    return artifact, batch


def preflight(
    values: list[dict[str, Any]], artifact_limit: int, batch_limit: int, count_limit: int
) -> dict[str, dict[str, Any]]:
    from ladon.proofir_v3 import _fail, _validate_envelope_shape, canonical_bytes

    if len(values) > count_limit:
        _fail("reference-valid", "batch-item-limit", "", f"v3 envelope batch exceeds item limit: {count_limit}")
    artifacts: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for value in values:
        _validate_envelope_shape(value)
        total_bytes += len(canonical_bytes(value, max_bytes=artifact_limit))
        if total_bytes > batch_limit:
            _fail("reference-valid", "batch-byte-limit", "", f"v3 envelope batch exceeds aggregate byte limit: {batch_limit}")
        _record(artifacts, value)
    return artifacts


def _record(artifacts: dict[str, dict[str, Any]], value: dict[str, Any]) -> None:
    from ladon.proofir_v3 import _fail, canonical_bytes

    artifact_id = str(value["artifactId"])
    prior = artifacts.get(artifact_id)
    if prior is not None and canonical_bytes(prior) != canonical_bytes(value):
        _fail("reference-valid", "duplicate-batch-artifact-id", "/artifactId", "different artifacts share a declared artifact ID", value)
    artifacts[artifact_id] = value
