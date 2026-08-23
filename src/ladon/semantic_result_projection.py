"""Compact, reference-closed projections of semantic proof-search results.

The semantic workers own canonical observations and ProofIR artifacts.  This
module only selects a bounded transport view of those observations; it never
reruns Lean, persists evidence, or promotes authority.  Callers must register
artifact bodies first and pass the resulting resolver mapping when requesting
``llm`` or ``review`` output.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from typing import Any

PROJECTION_NAMES = ("llm", "review", "audit")
DIRECT_PROJECTION_MAX_BYTES = 8 * 1024
DISCOVERY_PROJECTION_MAX_BYTES = 32 * 1024

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_CHECK_REF = re.compile(r"check:[0-9a-f]{64}")
_SEMANTIC_TERMINAL_STATUSES = frozenset({"accepted", "applicable-with-residuals", "rejected"})
_STRUCTURAL_KEYS = frozenset(
    {
        "artifacts",
        "candidateSubject",
        "subjectRefs",
        "termStructural",
        "typeStructural",
        "valueStructural",
    }
)


class SemanticProjectionError(ValueError):
    """Raised when a compact result would contain unresolved evidence."""


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

    operation = str(payload.get("operation", ""))
    if operation == "discover":
        projected = _project_discovery(payload, projection, registered_artifacts)
        maximum = DISCOVERY_PROJECTION_MAX_BYTES
    elif operation == "check-candidate":
        projected = _project_direct(payload, projection, registered_artifacts)
        maximum = DIRECT_PROJECTION_MAX_BYTES
    else:
        raise SemanticProjectionError(
            f"unsupported canonical semantic operation: {operation or '<missing>'}"
        )
    return _finalize_projection(projected, maximum)


def semantic_projection_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize exactly as the installed JSON CLI for byte-limit enforcement."""

    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _project_direct(
    payload: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    omissions: list[dict[str, Any]] = []
    subject = _receipt(payload).get("subject")
    subject = subject if isinstance(subject, Mapping) else {}
    candidate = _candidate_card(
        str(subject.get("candidate") or payload.get("candidate") or "<unknown>"),
        payload,
        {},
        projection,
        registry,
        omissions,
        pointer="/candidate",
    )
    status = str(payload.get("status", "unknown"))
    operational_failure = _check_operational_failure(payload)
    canonical_identity = _identity(payload)
    return {
        "schema": "ladon-semantic-candidate-projection-v1",
        "operation": "check-candidate",
        "status": status,
        "projection": _projection_header(
            projection,
            DIRECT_PROJECTION_MAX_BYTES,
            payload,
            canonical_identity,
        ),
        "request": _project_request(subject, projection, omissions, "/request"),
        "candidate": candidate,
        "coverage": {
            "candidatePopulation": {
                "observed": 1,
                "projected": 1,
                "omitted": 0,
                "statusCounts": {status: 1},
            },
            "operationalFailure": operational_failure,
        },
        "omissions": omissions,
        "limitations": _limitations(payload, projection, omissions),
    }


def _project_discovery(
    payload: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    omissions: list[dict[str, Any]] = []
    rows = payload.get("candidates")
    if not isinstance(rows, list):
        raise SemanticProjectionError("canonical discovery result has no candidate population")
    card_cap = 8 if projection == "llm" else 16
    selected = rows[:card_cap]
    if len(rows) > len(selected):
        _omit(
            omissions,
            "/candidates",
            "projection-collection-limit",
            len(rows) - len(selected),
        )
    candidates = [
        _candidate_card(
            str(row.get("name") or "<unknown>"),
            row.get("check") if isinstance(row.get("check"), Mapping) else {},
            row.get("shortlist") if isinstance(row.get("shortlist"), Mapping) else {},
            projection,
            registry,
            omissions,
            pointer=f"/candidates/{index}",
        )
        for index, row in enumerate(selected)
        if isinstance(row, Mapping)
    ]
    statuses = Counter(_candidate_status(row) for row in rows)
    scratch_statuses = Counter(
        scratch for row in rows if (scratch := _scratch_status(row)) is not None
    )
    request = payload.get("request")
    request = request if isinstance(request, Mapping) else {}
    canonical_identity = _identity(payload)
    return {
        "schema": "ladon-verified-discovery-projection-v1",
        "operation": "discover",
        "status": str(payload.get("status", "unknown")),
        "projection": _projection_header(
            projection,
            DISCOVERY_PROJECTION_MAX_BYTES,
            payload,
            canonical_identity,
        ),
        "request": _project_request(request, projection, omissions, "/request"),
        "candidates": candidates,
        "coverage": {
            "canonical": _safe_mapping(
                payload.get("coverage"), projection, omissions, "/coverage/canonical"
            ),
            "candidatePopulation": {
                "observed": len(rows),
                "projected": len(candidates),
                "omitted": len(rows) - len(candidates),
                "statusCounts": dict(sorted(statuses.items())),
                "scratchStatusCounts": dict(sorted(scratch_statuses.items())),
            },
            "operationalFailure": any(
                _check_operational_failure(row.get("check") if isinstance(row, Mapping) else {})
                for row in rows
            ),
        },
        "shortlist": _project_shortlist_summary(payload.get("shortlist"), projection, omissions),
        "ranking": _project_ranking(payload.get("ranking"), projection, omissions),
        "omissions": omissions,
        "limitations": _limitations(payload, projection, omissions),
    }


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


def _candidate_card(
    name: str,
    check: Mapping[str, Any],
    shortlist: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
    omissions: list[dict[str, Any]],
    *,
    pointer: str,
) -> dict[str, Any]:
    display_name = _bounded_text(name, 512, omissions, f"{pointer}/name")
    receipt = _receipt(check)
    environment, check_run = _evidence_refs(check, receipt, registry)
    result: dict[str, Any] = {
        "name": display_name,
        "nameFingerprint": _identity_text(name),
        "source": _source(shortlist, omissions, f"{pointer}/source"),
        "shortlist": _shortlist_card(shortlist, projection, omissions, f"{pointer}/shortlist"),
        "check": {
            "status": str(check.get("status", "unknown")),
            "applicationTerm": _optional_text(
                check.get("applicationTerm"),
                1024 if projection == "llm" else 1536,
                omissions,
                f"{pointer}/check/applicationTerm",
            ),
            "substitutions": _semantic_rows(
                check,
                "substitutions",
                projection,
                omissions,
                f"{pointer}/check/substitutions",
            ),
            "residualPremises": _semantic_rows(
                check,
                "residualPremises",
                projection,
                omissions,
                f"{pointer}/check/residualPremises",
            ),
            "dischargedHypotheses": _semantic_rows(
                check,
                "dischargedHypotheses",
                projection,
                omissions,
                f"{pointer}/check/dischargedHypotheses",
            ),
            "failure": _failure(check, projection, omissions, f"{pointer}/check/failure"),
            "authority": _authority(receipt, check),
            "environmentRef": environment,
            "checkRunRef": check_run,
            "scratch": _scratch_summary(
                check.get("scratch"),
                projection,
                registry,
                omissions,
                f"{pointer}/check/scratch",
            ),
        },
    }
    if projection == "review":
        result["check"]["resourceAccounting"] = _safe_mapping(
            check.get("resourceAccounting"),
            projection,
            omissions,
            f"{pointer}/check/resourceAccounting",
        )
        result["check"]["receiptIdentity"] = receipt.get("receiptIdentity")
    return result


def _evidence_refs(
    check: Mapping[str, Any],
    receipt: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    artifacts = check.get("artifacts")
    rows = (
        [row for row in artifacts if isinstance(row, Mapping)]
        if isinstance(artifacts, list)
        else []
    )
    environment_ref = check.get("environmentRef") or receipt.get("environmentRef")
    supplied_qualified = (
        check.get("checkRunRef") if isinstance(check.get("checkRunRef"), Mapping) else None
    )
    local_candidates = [
        check.get("checkRunId"),
        receipt.get("checkRunRef"),
        check.get("checkRunRef") if isinstance(check.get("checkRunRef"), str) else None,
        supplied_qualified.get("localId") if supplied_qualified is not None else None,
    ]
    local_refs = [value for value in local_candidates if value is not None]
    if len(set(local_refs)) > 1:
        raise SemanticProjectionError("semantic result contains contradictory check-run references")
    check_ref = local_refs[0] if local_refs else None
    environment_artifact = next(
        (
            row
            for row in rows
            if row.get("artifactKind") == "proofir.environment"
            and (environment_ref is None or row.get("environmentRef") == environment_ref)
        ),
        None,
    )
    check_artifact = next(
        (
            row
            for row in rows
            if row.get("artifactKind") == "proofir.check-run"
            and (
                check_ref is None
                or (
                    isinstance(row.get("payload"), Mapping)
                    and row["payload"].get("checkRunId") == check_ref
                )
            )
        ),
        None,
    )
    environment = _environment_reference(environment_ref, environment_artifact, registry)
    check_run = _check_reference(check_ref, check_artifact, registry)
    if supplied_qualified is not None and dict(supplied_qualified) != check_run:
        raise SemanticProjectionError(
            "semantic result artifact-qualified check-run reference is mismatched"
        )
    return environment, check_run


def _environment_reference(
    environment_ref: Any,
    artifact: Mapping[str, Any] | None,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, str] | None:
    if environment_ref is None and artifact is None:
        return None
    if not isinstance(environment_ref, str) or _DIGEST.fullmatch(environment_ref) is None:
        raise SemanticProjectionError("semantic result has an invalid environment reference")
    if artifact is None:
        raise SemanticProjectionError("semantic result environment reference is unresolved")
    artifact_id = _registered_artifact(artifact, "proofir.environment", registry)
    if artifact.get("environmentRef") != environment_ref:
        raise SemanticProjectionError("semantic result environment artifact is mismatched")
    return {"environmentRef": environment_ref, "artifactRef": artifact_id}


def _check_reference(
    check_ref: Any,
    artifact: Mapping[str, Any] | None,
    registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, str] | None:
    if check_ref is None and artifact is None:
        return None
    if not isinstance(check_ref, str) or _CHECK_REF.fullmatch(check_ref) is None:
        raise SemanticProjectionError("semantic result has an invalid check-run reference")
    if artifact is None:
        raise SemanticProjectionError("semantic result check-run reference is unresolved")
    artifact_id = _registered_artifact(artifact, "proofir.check-run", registry)
    payload = artifact.get("payload")
    if not isinstance(payload, Mapping) or payload.get("checkRunId") != check_ref:
        raise SemanticProjectionError("semantic result check-run artifact is mismatched")
    return {"artifactRef": artifact_id, "kind": "check-run", "localId": check_ref}


def _registered_artifact(
    artifact: Mapping[str, Any],
    expected_kind: str,
    registry: Mapping[str, Mapping[str, Any]],
) -> str:
    artifact_id = artifact.get("artifactId")
    if not isinstance(artifact_id, str) or _DIGEST.fullmatch(artifact_id) is None:
        raise SemanticProjectionError("semantic result contains an invalid artifact identity")
    registered = registry.get(artifact_id)
    if not isinstance(registered, Mapping):
        raise SemanticProjectionError(
            f"semantic evidence artifact is not registered: {artifact_id}"
        )
    if registered.get("artifactId", artifact_id) != artifact_id:
        raise SemanticProjectionError("semantic artifact resolver returned a mismatched identity")
    if (
        artifact.get("artifactKind") != expected_kind
        or registered.get("artifactKind", expected_kind) != expected_kind
    ):
        raise SemanticProjectionError("semantic artifact resolver returned a mismatched kind")
    return artifact_id


def _project_request(
    request: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any]:
    module = str(request.get("module", "<unknown>"))
    goal = str(request.get("goal", "<unknown>"))
    result: dict[str, Any] = {
        "module": _bounded_text(module, 512, omissions, f"{pointer}/module"),
        "moduleFingerprint": _identity_text(module),
        "goal": _bounded_text(goal, 1024, omissions, f"{pointer}/goal"),
        "goalFingerprint": _identity_text(goal),
        "localContext": _local_context(
            request.get("localContext"), projection, omissions, f"{pointer}/localContext"
        ),
    }
    for field in ("scope", "freshness", "scratchMode"):
        if request.get(field) is not None:
            result[field] = str(request[field])
    roots = request.get("roots")
    if isinstance(roots, list):
        result["roots"] = [str(item) for item in roots[:8]]
        if len(roots) > 8:
            _omit(omissions, f"{pointer}/roots", "projection-collection-limit", len(roots) - 8)
    return result


def _local_context(
    value: Any,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> list[dict[str, Any]]:
    rows = value if isinstance(value, list) else []
    limit = 4 if projection == "llm" else 8
    result = [
        {
            "name": _bounded_text(
                str(row.get("name", "")), 256, omissions, f"{pointer}/{index}/name"
            ),
            "type": _bounded_text(
                str(row.get("type", "")), 512, omissions, f"{pointer}/{index}/type"
            ),
        }
        for index, row in enumerate(rows[:limit])
        if isinstance(row, Mapping)
    ]
    if len(rows) > len(result):
        _omit(omissions, pointer, "projection-collection-limit", len(rows) - len(result))
    return result


def _semantic_rows(
    owner: Mapping[str, Any],
    field: str,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> list[Any] | None:
    if field not in owner:
        _omit(omissions, pointer, "canonical-field-unavailable", 1)
        return None
    value = owner.get(field)
    if not isinstance(value, list):
        _omit(omissions, pointer, "canonical-field-invalid", 1)
        return None
    limit = 4 if projection == "llm" else 6
    result = [
        _sanitize(row, projection, omissions, f"{pointer}/{index}")
        for index, row in enumerate(value[:limit])
    ]
    if len(value) > limit:
        _omit(omissions, pointer, "projection-collection-limit", len(value) - limit)
    return result


def _sanitize(
    value: Any,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
    *,
    depth: int = 0,
) -> Any:
    if depth > 6:
        _omit(omissions, pointer, "projection-depth-limit", 1)
        return None
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        keys = [key for key in sorted(value) if key not in _STRUCTURAL_KEYS]
        for key in keys[:24]:
            result[str(key)] = _sanitize(
                value[key], projection, omissions, f"{pointer}/{key}", depth=depth + 1
            )
        if len(keys) > 24:
            _omit(omissions, pointer, "projection-mapping-limit", len(keys) - 24)
        for key in value:
            if key in _STRUCTURAL_KEYS:
                _omit(omissions, f"{pointer}/{key}", "structural-evidence-omitted", 1)
        return result
    if isinstance(value, list):
        limit = 4 if projection == "llm" else 6
        result = [
            _sanitize(item, projection, omissions, f"{pointer}/{index}", depth=depth + 1)
            for index, item in enumerate(value[:limit])
        ]
        if len(value) > limit:
            _omit(omissions, pointer, "projection-collection-limit", len(value) - limit)
        return result
    if isinstance(value, str):
        return _bounded_text(value, 512, omissions, pointer)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _bounded_text(str(value), 512, omissions, pointer)


def _authority(receipt: Mapping[str, Any], check: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "executionBinding": receipt.get("executionBinding"),
        "observationState": receipt.get("observationState"),
        "operationOutcome": receipt.get("operationOutcome"),
        "authorityBasis": receipt.get("authorityBasis"),
        "analysisCompleteness": receipt.get(
            "analysisCompleteness", check.get("analysisCompleteness")
        ),
        "sourceFreshness": receipt.get("sourceFreshness"),
        "environmentMatch": receipt.get("environmentMatch"),
    }


def _failure(
    check: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any] | None:
    diagnostic = check.get("diagnostic")
    stage = check.get("failureStage")
    if not stage and isinstance(diagnostic, Mapping):
        stage = diagnostic.get("code")
    if not stage and not diagnostic:
        return None
    return {
        "stage": str(stage or "unspecified"),
        "diagnostic": _sanitize(diagnostic, projection, omissions, f"{pointer}/diagnostic"),
    }


def _scratch_summary(
    value: Any,
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    environment, check_run = _evidence_refs(value, _receipt(value), registry)
    result = {
        "status": str(value.get("status", "unknown")),
        "environmentRef": environment,
        "checkRunRef": check_run,
    }
    if value.get("diagnostic") is not None:
        result["diagnostic"] = _sanitize(
            value.get("diagnostic"), projection, omissions, f"{pointer}/diagnostic"
        )
    if environment is None and check_run is None:
        _omit(omissions, pointer, "scratch-evidence-unavailable", 1)
    return result


def _source(
    shortlist: Mapping[str, Any], omissions: list[dict[str, Any]], pointer: str
) -> dict[str, Any] | None:
    if not shortlist:
        _omit(omissions, pointer, "source-location-unavailable", 1)
        return None
    if not any(shortlist.get(key) is not None for key in ("module", "path", "line")):
        _omit(omissions, pointer, "source-location-unavailable", 1)
        return None
    return {
        "module": shortlist.get("module"),
        "path": shortlist.get("path"),
        "line": shortlist.get("line"),
    }


def _shortlist_card(
    shortlist: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any]:
    if not shortlist:
        return {"source": "explicit-candidate"}
    result: dict[str, Any] = {
        "ordinal": shortlist.get("shortlistOrdinal"),
        "bucket": shortlist.get("bucket"),
        "authority": shortlist.get("authority"),
        "fieldContributions": _safe_mapping(
            shortlist.get("fieldContributions"),
            projection,
            omissions,
            f"{pointer}/fieldContributions",
        ),
    }
    if projection == "review":
        for field in ("declarationId", "namespace", "package", "typeStatus", "verification"):
            if field in shortlist:
                result[field] = shortlist[field]
        for field in ("renderedType", "typeText", "conclusionText"):
            if shortlist.get(field) is not None:
                result[field] = _bounded_text(
                    str(shortlist[field]), 512, omissions, f"{pointer}/{field}"
                )
    return result


def _project_shortlist_summary(
    value: Any, projection: str, omissions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    allowed = ("source", "pattern", "coverage", "omissions", "freshnessEvidence")
    return {
        field: _sanitize(value[field], projection, omissions, f"/shortlist/{field}")
        for field in allowed
        if field in value
    }


def _project_ranking(
    value: Any, projection: str, omissions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    result = {"policy": value.get("policy")}
    contributions = value.get("contributions")
    if isinstance(contributions, list):
        limit = 8 if projection == "llm" else 16
        result["contributions"] = [
            _sanitize(row, projection, omissions, f"/ranking/contributions/{index}")
            for index, row in enumerate(contributions[:limit])
        ]
        if len(contributions) > limit:
            _omit(
                omissions,
                "/ranking/contributions",
                "projection-collection-limit",
                len(contributions) - limit,
            )
    return result


def _limitations(
    payload: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
) -> list[Any]:
    values: list[Any] = [
        "Artifact bodies and structural Lean expressions are omitted; expand registered evidence for audit.",
    ]
    for field in ("limitations", "nonclaims"):
        rows = payload.get(field)
        if isinstance(rows, list):
            values.extend(
                _sanitize(row, projection, omissions, f"/{field}/{index}")
                for index, row in enumerate(rows[:8])
            )
            if len(rows) > 8:
                _omit(omissions, f"/{field}", "projection-collection-limit", len(rows) - 8)
    return values


def _safe_mapping(
    value: Any,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    sanitized = _sanitize(value, projection, omissions, pointer)
    return sanitized if isinstance(sanitized, dict) else {}


def _receipt(owner: Mapping[str, Any]) -> Mapping[str, Any]:
    receipt = owner.get("evidenceReceipt")
    return receipt if isinstance(receipt, Mapping) else {}


def _candidate_status(row: Any) -> str:
    if not isinstance(row, Mapping) or not isinstance(row.get("check"), Mapping):
        return "invalid-candidate-row"
    return str(row["check"].get("status", "unknown"))


def _scratch_status(row: Any) -> str | None:
    if not isinstance(row, Mapping) or not isinstance(row.get("check"), Mapping):
        return None
    scratch = row["check"].get("scratch")
    return str(scratch.get("status", "unknown")) if isinstance(scratch, Mapping) else None


def _check_operational_failure(check: Mapping[str, Any]) -> bool:
    if check.get("status") not in _SEMANTIC_TERMINAL_STATUSES:
        return True
    scratch = check.get("scratch")
    return isinstance(scratch, Mapping) and scratch.get("status") != "compiled"


def _finalize_projection(payload: dict[str, Any], maximum: int) -> dict[str, Any]:
    _fit_projection(payload, maximum - 128)
    payload["projection"]["projectionIdentity"] = _identity(payload)
    size = len(semantic_projection_bytes(payload))
    if size > maximum:
        raise SemanticProjectionError(
            f"semantic {payload['operation']} projection exceeds its {maximum}-byte cap"
        )
    return payload


def _fit_projection(payload: dict[str, Any], maximum: int) -> None:
    candidates_key = "candidates" if isinstance(payload.get("candidates"), list) else None
    if candidates_key is not None:
        candidates = payload[candidates_key]
        while len(semantic_projection_bytes(payload)) > maximum and len(candidates) > 1:
            candidates.pop()
            removed_prefix = f"/candidates/{len(candidates)}"
            payload["omissions"][:] = [
                row
                for row in payload["omissions"]
                if not str(row.get("pointer", "")).startswith(removed_prefix)
            ]
            ranking = payload.get("ranking")
            if isinstance(ranking, Mapping) and isinstance(ranking.get("contributions"), list):
                ranking["contributions"] = ranking["contributions"][: len(candidates)]
            population = payload["coverage"]["candidatePopulation"]
            population["projected"] = len(candidates)
            population["omitted"] = population["observed"] - len(candidates)
            _omit(payload["omissions"], "/candidates", "projection-byte-limit", 1)
    if len(semantic_projection_bytes(payload)) <= maximum:
        return
    cards = payload.get("candidates") or [payload.get("candidate")]
    for index, card in enumerate(cards):
        if not isinstance(card, Mapping) or not isinstance(card.get("check"), dict):
            continue
        check = card["check"]
        card_pointer = f"/candidates/{index}" if candidates_key is not None else "/candidate"
        for field in ("substitutions", "residualPremises", "dischargedHypotheses"):
            rows = check.get(field)
            if isinstance(rows, list) and rows:
                _omit(
                    payload["omissions"],
                    f"{card_pointer}/check/{field}",
                    "projection-byte-limit",
                    len(rows),
                )
                check[field] = []
        if isinstance(check.get("applicationTerm"), str):
            check["applicationTerm"] = _truncate_utf8(check["applicationTerm"], 256)
    if len(semantic_projection_bytes(payload)) <= maximum:
        return
    request = payload.get("request")
    if isinstance(request, dict):
        if request.get("localContext"):
            _omit(
                payload["omissions"],
                "/request/localContext",
                "projection-byte-limit",
                len(request["localContext"]),
            )
            request["localContext"] = []
        for field in ("goal", "module"):
            if isinstance(request.get(field), str):
                request[field] = _truncate_utf8(request[field], 128)


def _optional_text(
    value: Any,
    limit: int,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> str | None:
    return None if value is None else _bounded_text(str(value), limit, omissions, pointer)


def _bounded_text(
    value: str,
    limit: int,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= limit:
        return value
    _omit(omissions, pointer, "projection-text-byte-limit", len(encoded) - limit)
    return _truncate_utf8(value, limit)


def _truncate_utf8(value: str, limit: int) -> str:
    if len(value.encode("utf-8")) <= limit:
        return value
    marker = "…"
    room = max(0, limit - len(marker.encode("utf-8")))
    raw = value.encode("utf-8")[:room]
    while raw:
        try:
            return raw.decode("utf-8") + marker
        except UnicodeDecodeError:
            raw = raw[:-1]
    return marker if limit >= len(marker.encode("utf-8")) else ""


def _omit(omissions: list[dict[str, Any]], pointer: str, reason: str, omitted: int) -> None:
    for row in omissions:
        if row["pointer"] == pointer and row["reason"] == reason:
            row["omitted"] += omitted
            return
    omissions.append({"pointer": pointer, "reason": reason, "omitted": omitted})
    omissions.sort(key=lambda row: (row["pointer"], row["reason"]))


def _identity(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _identity_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "DIRECT_PROJECTION_MAX_BYTES",
    "DISCOVERY_PROJECTION_MAX_BYTES",
    "PROJECTION_NAMES",
    "SemanticProjectionError",
    "project_semantic_result",
    "semantic_projection_bytes",
]
