"""Compact, reference-closed projections of semantic proof-search results.

The semantic workers own canonical observations and ProofIR artifacts.  This
module only selects a bounded transport view of those observations; it never
reruns Lean, persists evidence, or promotes authority.  Callers must register
artifact bodies first and pass the resulting resolver mapping when requesting
``llm`` or ``review`` output.
"""

from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Mapping
from typing import Any

from ladon._semantic_observation_population import validate_discovery_aggregate
from ladon.semantic_observation_closure import validate_semantic_observation_population
from ladon.semantic_projection_cards import (
    candidate_card,
    candidate_status,
    check_operational_failure,
    limitations,
    project_ranking,
    project_request,
    project_shortlist_summary,
    receipt,
    scratch_status,
)
from ladon.semantic_projection_core import (
    DIRECT_PROJECTION_MAX_BYTES,
    DISCOVERY_PROJECTION_MAX_BYTES,
    PROJECTION_NAMES,
    SemanticProjectionError,
    identity,
    omit,
    semantic_projection_bytes,
)
from ladon.semantic_projection_fit import finalize_projection


def project_semantic_result(
    payload: Mapping[str, Any],
    *,
    projection: str = "audit",
    registered_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return one deterministic semantic-result projection.

    ``audit`` is a compatibility projection: it returns a detached copy with
    the canonical schema and fields unchanged.  Compact projections require a
    caller-owned resolver containing every environment/check artifact named by
    the emitted references.
    """

    if projection not in PROJECTION_NAMES:
        raise SemanticProjectionError(f"unsupported semantic projection: {projection}")
    if projection == "audit":
        return copy.deepcopy(dict(payload))
    if registered_artifacts is None:
        raise SemanticProjectionError(
            "compact semantic projections require a registered artifact resolver"
        )
    validate_semantic_observation_population(payload, registered_artifacts)
    projected, maximum = _compact_projection(payload, projection, registered_artifacts)
    return finalize_projection(projected, maximum)


def _compact_projection(
    payload: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], int]:
    operation = str(payload.get("operation", ""))
    if operation == "discover":
        return _project_discovery(payload, projection, registry), DISCOVERY_PROJECTION_MAX_BYTES
    if operation == "check-candidate":
        return _project_direct(payload, projection, registry), DIRECT_PROJECTION_MAX_BYTES
    raise SemanticProjectionError(
        f"unsupported canonical semantic operation: {operation or '<missing>'}"
    )


def _project_direct(
    payload: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    omissions: list[dict[str, Any]] = []
    subject = receipt(payload).get("subject")
    subject = subject if isinstance(subject, Mapping) else {}
    candidate = candidate_card(
        str(subject.get("candidate") or payload.get("candidate") or "<unknown>"),
        payload,
        {},
        projection,
        registry,
        omissions,
        pointer="/candidate",
    )
    status = str(payload.get("status", "unknown"))
    return {
        "schema": "ladon-semantic-candidate-projection-v1",
        "operation": "check-candidate",
        "status": status,
        "projection": _projection_header(
            projection,
            DIRECT_PROJECTION_MAX_BYTES,
            payload,
            identity(payload),
        ),
        "request": project_request(subject, projection, omissions, "/request"),
        "candidate": candidate,
        "coverage": _direct_coverage(payload, status),
        "omissions": omissions,
        "limitations": limitations(payload, projection, omissions),
    }


def _direct_coverage(payload: Mapping[str, Any], status: str) -> dict[str, Any]:
    return {
        "candidatePopulation": {
            "observed": 1,
            "projected": 1,
            "omitted": 0,
            "statusCounts": {status: 1},
        },
        "operationalFailure": check_operational_failure(payload),
    }


def _project_discovery(
    payload: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    omissions: list[dict[str, Any]] = []
    rows = _discovery_rows(payload)
    candidates = _project_candidate_population(rows, projection, registry, omissions)
    request = payload.get("request")
    request = request if isinstance(request, Mapping) else {}
    return {
        "schema": "ladon-verified-discovery-projection-v1",
        "operation": "discover",
        "status": str(payload.get("status", "unknown")),
        "projection": _projection_header(
            projection,
            DISCOVERY_PROJECTION_MAX_BYTES,
            payload,
            identity(payload),
        ),
        "request": project_request(request, projection, omissions, "/request"),
        "candidates": candidates,
        "coverage": _discovery_coverage(payload, rows, len(candidates), projection, omissions),
        "shortlist": project_shortlist_summary(payload.get("shortlist"), projection, omissions),
        "ranking": project_ranking(payload.get("ranking"), projection, omissions),
        "omissions": omissions,
        "limitations": limitations(payload, projection, omissions),
    }


def _discovery_rows(payload: Mapping[str, Any]) -> list[Any]:
    rows = payload.get("candidates")
    if not isinstance(rows, list):
        raise SemanticProjectionError("canonical discovery result has no candidate population")
    return rows


def _project_candidate_population(
    rows: list[Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
    omissions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    limit = 8 if projection == "llm" else 16
    selected = rows[:limit]
    if len(rows) > len(selected):
        omit(omissions, "/candidates", "projection-collection-limit", len(rows) - len(selected))
    return [
        _project_candidate_row(row, index, projection, registry, omissions)
        for index, row in enumerate(selected)
        if isinstance(row, Mapping)
    ]


def _project_candidate_row(
    row: Mapping[str, Any],
    index: int,
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
    omissions: list[dict[str, Any]],
) -> dict[str, Any]:
    check = row.get("check")
    shortlist = row.get("shortlist")
    return candidate_card(
        str(row.get("name") or "<unknown>"),
        check if isinstance(check, Mapping) else {},
        shortlist if isinstance(shortlist, Mapping) else {},
        projection,
        registry,
        omissions,
        pointer=f"/candidates/{index}",
    )


def _discovery_coverage(
    payload: Mapping[str, Any],
    rows: list[Any],
    projected_count: int,
    projection: str,
    omissions: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = Counter(candidate_status(row) for row in rows)
    scratch_statuses = Counter(
        status for row in rows if (status := scratch_status(row)) is not None
    )
    return {
        "canonical": validate_discovery_aggregate(payload),
        "candidatePopulation": {
            "observed": len(rows),
            "projected": projected_count,
            "omitted": len(rows) - projected_count,
            "statusCounts": dict(sorted(statuses.items())),
            "scratchStatusCounts": dict(sorted(scratch_statuses.items())),
        },
        "operationalFailure": any(_row_operational_failure(row) for row in rows),
    }


def _row_operational_failure(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return check_operational_failure({})
    check = row.get("check")
    return check_operational_failure(check if isinstance(check, Mapping) else {})


def _projection_header(
    projection: str,
    maximum: int,
    payload: Mapping[str, Any],
    canonical_identity: str,
) -> dict[str, Any]:
    return {
        "name": projection,
        "canonicalSchema": payload.get("schema"),
        "canonicalPayloadIdentity": canonical_identity,
        "producerResultIdentity": payload.get("resultIdentity"),
        "limits": {
            "maxBytes": maximum,
            "measurement": "pretty-json-utf8-v1",
        },
    }


__all__ = [
    "DIRECT_PROJECTION_MAX_BYTES",
    "DISCOVERY_PROJECTION_MAX_BYTES",
    "PROJECTION_NAMES",
    "SemanticProjectionError",
    "project_semantic_result",
    "semantic_projection_bytes",
]
