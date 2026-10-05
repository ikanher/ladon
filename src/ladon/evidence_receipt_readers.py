"""Receipt projections for canonical checks and read-only theorem selectors."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.evidence_receipt import (
    build_evidence_receipt,
    project_evidence_receipt,
    validate_evidence_receipt,
)
from ladon.proofir_v3 import validate_envelope
from ladon.semantic_execution_binding import (
    UNRECORDED_EXECUTION,
    project_recorded_execution_receipt,
    validate_recorded_execution_binding,
)
from ladon.semantic_stored_receipt import validate_stored_observation_receipt


def stored_check_receipt(
    artifact: Mapping[str, Any], *, projection_kind: str = "sqlite-row",
    environment_artifacts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any] | None:
    """Project an optional canonical check receipt, rejecting malformed owners."""

    try:
        observation = artifact.get("extensions", {}).get("ladon.process-observation/v1", {})
        receipt = observation.get("evidenceReceipt")
        if receipt is None:
            return None
        canonical = validate_envelope(dict(artifact)).to_dict()
        payload = canonical["payload"]
        if (
            canonical["artifactKind"] != "proofir.check-run"
            or receipt.get("environmentRef") != canonical["environmentRef"]
            or receipt.get("checkRunRef") != payload.get("checkRunId")
            or receipt.get("authorityBasis") != payload.get("guarantee", {}).get("authorityBasis")
        ):
            raise ValueError("stored receipt does not match its canonical check owner")
        validate_evidence_receipt(receipt)
        validate_stored_observation_receipt(canonical, receipt)
        recorded = validate_recorded_execution_binding(canonical, receipt, environment_artifacts)
        return project_recorded_execution_receipt(
            receipt, projection_kind=projection_kind, recorded=recorded,
        )
    except (TypeError, KeyError, AttributeError) as error:
        raise ValueError("stored check receipt or owner is malformed") from error


def stored_query_receipt(
    query_kind: str, theorem: str, *, observed: bool, source_ref: str | None = None,
    source_freshness: str = "not-assessed", projection_kind: str = "dossier",
) -> dict[str, Any]:
    """Attribute a stored query without inventing historical checker execution."""

    parent = build_evidence_receipt(
        subject={"queryKind": query_kind, "theorem": theorem, "sourceRef": source_ref},
        execution_binding="none", observation_state="stored" if observed else "absent",
        operation_outcome="not-run", authority_basis="stored-observation" if observed else "not-assessed",
        analysis_completeness="not-assessed", source_freshness=source_freshness,
        environment_match="not-assessed",
        limitations=["This query does not run a theorem check or establish theorem truth."],
    )
    return project_evidence_receipt(parent, projection_kind=projection_kind)


def receipt_text_lines(receipt: Mapping[str, Any] | None) -> list[str]:
    """Render validated dimensions without shortening exact receipt identities."""

    if receipt is None:
        return []
    projected = project_evidence_receipt(receipt, projection_kind="text-renderer")
    fields = (
        "executionBinding", "observationState", "operationOutcome", "sourceFreshness",
        "environmentMatch", "authorityBasis", "analysisCompleteness",
    )
    lines = [
        f"evidenceReceipt: {projected['receiptIdentity']}",
        "evidence dimensions: " + ", ".join(f"{field}={projected[field]}" for field in fields),
    ]
    if UNRECORDED_EXECUTION in projected["limitations"]:
        lines.append(f"execution binding limitation: {UNRECORDED_EXECUTION}")
    return lines


def derivation_query_receipt(
    artifact_ref: str, request: Mapping[str, Any], *, invalid: bool,
) -> dict[str, Any]:
    """Bind a stored structural query to its content owner and exact inputs."""

    encoded = json.dumps(dict(request), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return build_evidence_receipt(
        subject={
            "queryKind": "derivation", "artifactRef": artifact_ref,
            "queryIdentity": "sha256:" + hashlib.sha256(encoded.encode()).hexdigest(),
        },
        execution_binding="none", observation_state="failed" if invalid else "derived",
        operation_outcome="not-run",
        authority_basis="not-assessed" if invalid else "stored-observation",
        analysis_completeness="not-assessed", source_freshness="not-assessed",
        environment_match="not-assessed",
        limitations=["Structural derivation analysis does not run a theorem check."],
    )
