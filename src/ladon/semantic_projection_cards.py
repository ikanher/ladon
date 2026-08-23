"""Candidate, request, ranking, and limitation cards for semantic projections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.semantic_projection_core import (
    bounded_text,
    identity_text,
    omit,
    optional_text,
    safe_mapping,
    sanitize,
)
from ladon.semantic_projection_evidence import evidence_refs

_SEMANTIC_TERMINAL_STATUSES = frozenset(
    {"accepted", "applicable-with-residuals", "rejected"}
)


def candidate_card(
    name: str,
    check: Mapping[str, Any],
    shortlist: Mapping[str, Any],
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
    omissions: list[dict[str, Any]],
    *,
    pointer: str,
) -> dict[str, Any]:
    """Project one canonical candidate observation."""

    display_name = bounded_text(name, 512, omissions, f"{pointer}/name")
    evidence_receipt = receipt(check)
    environment, check_run = evidence_refs(check, evidence_receipt, registry)
    result: dict[str, Any] = {
        "name": display_name,
        "nameFingerprint": identity_text(name),
        "source": _source(shortlist, omissions, f"{pointer}/source"),
        "shortlist": _shortlist_card(
            shortlist, projection, omissions, f"{pointer}/shortlist"
        ),
        "check": _check_card(
            check,
            evidence_receipt,
            environment,
            check_run,
            projection,
            registry,
            omissions,
            pointer,
        ),
    }
    return result


def _check_card(
    check: Mapping[str, Any],
    evidence_receipt: Mapping[str, Any],
    environment: dict[str, str] | None,
    check_run: dict[str, str] | None,
    projection: str,
    registry: Mapping[str, Mapping[str, Any]],
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": str(check.get("status", "unknown")),
        "applicationTerm": optional_text(
            check.get("applicationTerm"),
            1024 if projection == "llm" else 1536,
            omissions,
            f"{pointer}/check/applicationTerm",
        ),
        "substitutions": _semantic_rows(
            check, "substitutions", projection, omissions, f"{pointer}/check/substitutions"
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
        "authority": _authority(evidence_receipt, check),
        "environmentRef": environment,
        "checkRunRef": check_run,
        "scratch": _scratch_summary(
            check.get("scratch"),
            projection,
            registry,
            omissions,
            f"{pointer}/check/scratch",
        ),
    }
    if projection == "review":
        result["resourceAccounting"] = safe_mapping(
            check.get("resourceAccounting"),
            projection,
            omissions,
            f"{pointer}/check/resourceAccounting",
        )
        result["receiptIdentity"] = evidence_receipt.get("receiptIdentity")
    return result


def project_request(
    request: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> dict[str, Any]:
    """Project a semantic request with bounded text and local context."""

    module = str(request.get("module", "<unknown>"))
    goal = str(request.get("goal", "<unknown>"))
    result: dict[str, Any] = {
        "module": bounded_text(module, 512, omissions, f"{pointer}/module"),
        "moduleFingerprint": identity_text(module),
        "goal": bounded_text(goal, 1024, omissions, f"{pointer}/goal"),
        "goalFingerprint": identity_text(goal),
        "localContext": _local_context(
            request.get("localContext"), projection, omissions, f"{pointer}/localContext"
        ),
    }
    _copy_request_modes(request, result)
    _project_roots(request.get("roots"), result, omissions, pointer)
    return result


def _copy_request_modes(request: Mapping[str, Any], result: dict[str, Any]) -> None:
    for field in ("scope", "freshness", "scratchMode"):
        if request.get(field) is not None:
            result[field] = str(request[field])


def _project_roots(
    value: Any,
    result: dict[str, Any],
    omissions: list[dict[str, Any]],
    pointer: str,
) -> None:
    if not isinstance(value, list):
        return
    result["roots"] = [str(item) for item in value[:8]]
    if len(value) > 8:
        omit(omissions, f"{pointer}/roots", "projection-collection-limit", len(value) - 8)


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
            "name": bounded_text(
                str(row.get("name", "")), 256, omissions, f"{pointer}/{index}/name"
            ),
            "type": bounded_text(
                str(row.get("type", "")), 512, omissions, f"{pointer}/{index}/type"
            ),
        }
        for index, row in enumerate(rows[:limit])
        if isinstance(row, Mapping)
    ]
    if len(rows) > len(result):
        omit(omissions, pointer, "projection-collection-limit", len(rows) - len(result))
    return result


def _semantic_rows(
    owner: Mapping[str, Any],
    field: str,
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> list[Any] | None:
    if field not in owner:
        omit(omissions, pointer, "canonical-field-unavailable", 1)
        return None
    value = owner.get(field)
    if not isinstance(value, list):
        omit(omissions, pointer, "canonical-field-invalid", 1)
        return None
    limit = 4 if projection == "llm" else 6
    result = [
        sanitize(row, projection, omissions, f"{pointer}/{index}")
        for index, row in enumerate(value[:limit])
    ]
    if len(value) > limit:
        omit(omissions, pointer, "projection-collection-limit", len(value) - limit)
    return result


def _authority(receipt_row: Mapping[str, Any], check: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "executionBinding": receipt_row.get("executionBinding"),
        "observationState": receipt_row.get("observationState"),
        "operationOutcome": receipt_row.get("operationOutcome"),
        "authorityBasis": receipt_row.get("authorityBasis"),
        "analysisCompleteness": receipt_row.get(
            "analysisCompleteness", check.get("analysisCompleteness")
        ),
        "sourceFreshness": receipt_row.get("sourceFreshness"),
        "environmentMatch": receipt_row.get("environmentMatch"),
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
        "diagnostic": sanitize(diagnostic, projection, omissions, f"{pointer}/diagnostic"),
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
    environment, check_run = evidence_refs(value, receipt(value), registry)
    result = {
        "status": str(value.get("status", "unknown")),
        "environmentRef": environment,
        "checkRunRef": check_run,
    }
    _copy_scratch_diagnostic(value, result, projection, omissions, pointer)
    if environment is None and check_run is None:
        omit(omissions, pointer, "scratch-evidence-unavailable", 1)
    return result


def _copy_scratch_diagnostic(
    value: Mapping[str, Any],
    result: dict[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> None:
    if value.get("diagnostic") is not None:
        result["diagnostic"] = sanitize(
            value.get("diagnostic"), projection, omissions, f"{pointer}/diagnostic"
        )


def _source(
    shortlist: Mapping[str, Any], omissions: list[dict[str, Any]], pointer: str
) -> dict[str, Any] | None:
    if not shortlist:
        omit(omissions, pointer, "source-location-unavailable", 1)
        return None
    if not any(shortlist.get(key) is not None for key in ("module", "path", "line")):
        omit(omissions, pointer, "source-location-unavailable", 1)
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
        "fieldContributions": safe_mapping(
            shortlist.get("fieldContributions"),
            projection,
            omissions,
            f"{pointer}/fieldContributions",
        ),
    }
    if projection == "review":
        _copy_review_shortlist_fields(shortlist, result, omissions, pointer)
    return result


def _copy_review_shortlist_fields(
    shortlist: Mapping[str, Any],
    result: dict[str, Any],
    omissions: list[dict[str, Any]],
    pointer: str,
) -> None:
    for field in ("declarationId", "namespace", "package", "typeStatus", "verification"):
        if field in shortlist:
            result[field] = shortlist[field]
    for field in ("renderedType", "typeText", "conclusionText"):
        if shortlist.get(field) is not None:
            result[field] = bounded_text(
                str(shortlist[field]), 512, omissions, f"{pointer}/{field}"
            )


def project_shortlist_summary(
    value: Any, projection: str, omissions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Project the bounded shortlist acquisition summary."""

    if not isinstance(value, Mapping):
        return None
    allowed = ("source", "pattern", "coverage", "omissions", "freshnessEvidence")
    return {
        field: sanitize(value[field], projection, omissions, f"/shortlist/{field}")
        for field in allowed
        if field in value
    }


def project_ranking(
    value: Any, projection: str, omissions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Project ranking policy and its bounded candidate contributions."""

    if not isinstance(value, Mapping):
        return None
    result = {"policy": value.get("policy")}
    contributions = value.get("contributions")
    if not isinstance(contributions, list):
        return result
    limit = 8 if projection == "llm" else 16
    result["contributions"] = [
        sanitize(row, projection, omissions, f"/ranking/contributions/{index}")
        for index, row in enumerate(contributions[:limit])
    ]
    if len(contributions) > limit:
        omit(
            omissions,
            "/ranking/contributions",
            "projection-collection-limit",
            len(contributions) - limit,
        )
    return result


def limitations(
    payload: Mapping[str, Any],
    projection: str,
    omissions: list[dict[str, Any]],
) -> list[Any]:
    """Merge canonical limitations and nonclaims into one bounded list."""

    values: list[Any] = [
        "Artifact bodies and structural Lean expressions are omitted; expand registered evidence for audit.",
    ]
    for field in ("limitations", "nonclaims"):
        _extend_limitations(values, payload, field, projection, omissions)
    return values


def _extend_limitations(
    values: list[Any],
    payload: Mapping[str, Any],
    field: str,
    projection: str,
    omissions: list[dict[str, Any]],
) -> None:
    rows = payload.get(field)
    if not isinstance(rows, list):
        return
    values.extend(
        sanitize(row, projection, omissions, f"/{field}/{index}")
        for index, row in enumerate(rows[:8])
    )
    if len(rows) > 8:
        omit(omissions, f"/{field}", "projection-collection-limit", len(rows) - 8)


def receipt(owner: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a canonical evidence receipt or an empty mapping."""

    value = owner.get("evidenceReceipt")
    return value if isinstance(value, Mapping) else {}


def candidate_status(row: Any) -> str:
    """Return the public semantic status of one discovery row."""

    if not isinstance(row, Mapping) or not isinstance(row.get("check"), Mapping):
        return "invalid-candidate-row"
    return str(row["check"].get("status", "unknown"))


def scratch_status(row: Any) -> str | None:
    """Return the scratch status of one discovery row, when present."""

    if not isinstance(row, Mapping) or not isinstance(row.get("check"), Mapping):
        return None
    scratch = row["check"].get("scratch")
    return str(scratch.get("status", "unknown")) if isinstance(scratch, Mapping) else None


def check_operational_failure(check: Mapping[str, Any]) -> bool:
    """Return whether a candidate or requested scratch ended operationally."""

    if check.get("status") not in _SEMANTIC_TERMINAL_STATUSES:
        return True
    scratch = check.get("scratch")
    return isinstance(scratch, Mapping) and scratch.get("status") != "compiled"


__all__ = [
    "candidate_card",
    "candidate_status",
    "check_operational_failure",
    "limitations",
    "project_ranking",
    "project_request",
    "project_shortlist_summary",
    "receipt",
    "scratch_status",
]
