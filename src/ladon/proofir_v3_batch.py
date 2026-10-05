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
) -> tuple[list[tuple[dict[str, Any], bytes]], dict[str, dict[str, Any]]]:
    from ladon.proofir_v3 import _fail, _prepare_envelope

    if len(values) > count_limit:
        _fail("reference-valid", "batch-item-limit", "", f"v3 envelope batch exceeds item limit: {count_limit}")
    artifacts: dict[str, dict[str, Any]] = {}
    encodings: dict[str, bytes] = {}
    rows: list[tuple[dict[str, Any], bytes]] = []
    total_bytes = 0
    for value in values:
        owned, encoded = _prepare_envelope(value, artifact_limit)
        total_bytes += len(encoded)
        if total_bytes > batch_limit:
            _fail("reference-valid", "batch-byte-limit", "", f"v3 envelope batch exceeds aggregate byte limit: {batch_limit}")
        artifact_id = owned["artifactId"]
        prior = encodings.get(artifact_id)
        if prior is not None and prior != encoded:
            _fail("reference-valid", "duplicate-batch-artifact-id", "/artifactId", "different artifacts share a declared artifact ID", owned)
        artifacts[artifact_id] = owned
        encodings[artifact_id] = encoded
        rows.append((owned, encoded))
    return rows, artifacts
