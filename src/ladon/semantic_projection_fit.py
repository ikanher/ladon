"""Deterministic byte-budget fitting for semantic-result projections."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from ladon.semantic_projection_core import (
    SemanticProjectionError,
    identity,
    identity_text,
    omit,
    semantic_projection_bytes,
    truncate_utf8,
)

_SEMANTIC_ROW_FIELDS = ("substitutions", "residualPremises", "dischargedHypotheses")
_OMISSION_LEDGER_LIMIT = 24


def finalize_projection(payload: dict[str, Any], maximum: int) -> dict[str, Any]:
    """Fit, identify, and enforce one projection's public byte cap."""

    payload, ready = _compact_application_ledger(payload, maximum - 128)
    if not ready:
        fit_projection(payload, maximum - 128)
        _bound_omission_ledger(payload, _OMISSION_LEDGER_LIMIT)
    if not _fits(payload, maximum - 128):
        payload = _minimal_projection(payload)
    payload["projection"]["projectionIdentity"] = identity(payload)
    size = len(semantic_projection_bytes(payload))
    if size > maximum:
        raise SemanticProjectionError(
            f"semantic {payload['operation']} projection exceeds its {maximum}-byte cap"
        )
    return payload


def _compact_application_ledger(payload, maximum):
    candidate = payload.get("candidate")
    if not isinstance(candidate, Mapping):
        return payload, False
    check = candidate.get("check")
    if not isinstance(check, Mapping) or check.get("applicationObservationVersion") != 4:
        return payload, False
    # Try a bounded disclosure ledger before discarding the mathematical view.
    # Preserve original population counts, and leave the original untouched if
    # the candidate still cannot fit. Larger inputs use the existing fallback.
    compact = copy.deepcopy(payload)
    _bound_omission_ledger(compact, 5)
    if _fits(compact, maximum):
        return compact, True
    return payload, False


def fit_projection(payload: dict[str, Any], maximum: int) -> None:
    """Remove bounded optional detail until a projection fits its budget."""

    has_candidate_population = isinstance(payload.get("candidates"), list)
    if has_candidate_population:
        _trim_candidate_population(payload, maximum)
    if _fits(payload, maximum):
        return
    _trim_candidate_cards(payload, has_candidate_population)
    if _fits(payload, maximum):
        return
    _trim_request(payload)


def _bound_omission_ledger(payload: dict[str, Any], limit: int) -> None:
    rows = payload.get("omissions")
    if not isinstance(rows, list):
        rows = []
    observed = len(rows)
    total_claims = sum(_omitted_claims(row) for row in rows)
    projected = min(observed, limit)
    generated = 0
    if observed > limit:
        projected = max(0, limit - 1)
        rows = [*rows[:projected], _omission_summary(observed - projected)]
        rows.sort(key=lambda row: (str(row.get("pointer")), str(row.get("reason"))))
        generated = 1
    payload["omissions"] = rows
    coverage = payload.get("coverage")
    if isinstance(coverage, dict):
        coverage["omissionPopulation"] = {
            "observedRecords": observed,
            "projectedRecords": projected,
            "omittedRecords": observed - projected,
            "generatedRecords": generated,
            "transportRecords": len(rows),
            "totalClaims": total_claims,
        }


def _omitted_claims(row: Any) -> int:
    if not isinstance(row, Mapping):
        return 0
    value = row.get("omitted")
    return value if isinstance(value, int) and value > 0 else 0


def _omission_summary(omitted: int) -> dict[str, Any]:
    return {
        "pointer": "/omissions",
        "reason": "projection-collection-limit",
        "omitted": omitted,
    }


def _minimal_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Retain the authority-bearing compact skeleton as a last resort."""

    omissions = payload.get("omissions")
    rows = omissions if isinstance(omissions, list) else []
    limitation_rows = payload.get("limitations")
    limitation_rows = limitation_rows if isinstance(limitation_rows, list) else []
    status = str(payload.get("status", "unknown"))
    result: dict[str, Any] = {
        "schema": payload.get("schema"),
        "operation": payload.get("operation"),
        "status": truncate_utf8(status, 128),
        "statusFingerprint": identity_text(status),
        "projection": _minimal_projection_header(payload.get("projection")),
        "request": _minimal_request(payload.get("request")),
        "coverage": _minimal_coverage(payload.get("coverage"), rows),
        "omissions": [
            {
                "pointer": "/projection",
                "reason": "projection-byte-limit",
                "omitted": 1,
            }
        ],
        "requiresAuditExpansion": True,
        "limitationCount": len(limitation_rows),
        "limitationsFingerprint": identity({"limitations": limitation_rows}),
    }
    _copy_minimal_candidates(payload, result)
    return result


def _minimal_projection_header(value: Any) -> dict[str, Any]:
    row = value if isinstance(value, Mapping) else {}
    result = {
        "canonicalPayloadIdentity": row.get("canonicalPayloadIdentity"),
        "limits": row.get("limits"),
    }
    _copy_minimal_identity_text(result, "name", row.get("name"), 32)
    _copy_minimal_identity_text(
        result, "canonicalSchema", row.get("canonicalSchema"), 128
    )
    _copy_minimal_identity_text(
        result, "producerResultIdentity", row.get("producerResultIdentity"), 128
    )
    return result


def _minimal_request(value: Any) -> dict[str, Any]:
    row = value if isinstance(value, Mapping) else {}
    result = {
        field: row[field]
        for field in ("moduleFingerprint", "goalFingerprint")
        if field in row
    }
    for field in ("scope", "freshness", "scratchMode"):
        _copy_minimal_identity_text(result, field, row.get(field), 64)
    return result


def _copy_minimal_identity_text(
    result: dict[str, Any], field: str, value: Any, limit: int
) -> None:
    if value is None:
        return
    text = str(value)
    result[field] = truncate_utf8(text, limit)
    result[f"{field}Fingerprint"] = identity_text(text)


def _minimal_coverage(value: Any, omissions: list[Any]) -> dict[str, Any]:
    row = value if isinstance(value, Mapping) else {}
    canonical = row.get("canonical")
    result = {
        "canonical": _minimal_canonical_coverage(canonical),
        "canonicalIdentity": identity(canonical) if isinstance(canonical, Mapping) else None,
        "candidatePopulation": row.get("candidatePopulation"),
        "operationalFailure": row.get("operationalFailure"),
    }
    prior = row.get("omissionPopulation")
    prior = prior if isinstance(prior, Mapping) else {}
    result["omissionPopulation"] = {
        "observedRecords": prior.get("observedRecords", len(omissions)),
        "projectedRecords": 0,
        "omittedRecords": prior.get("observedRecords", len(omissions)),
        "generatedRecords": 1,
        "transportRecords": 1,
        "totalClaims": prior.get(
            "totalClaims", sum(_omitted_claims(item) for item in omissions)
        ),
    }
    return result


def _minimal_canonical_coverage(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    fields = (
        "shortlisted",
        "submitted",
        "completed",
        "accepted",
        "rejected",
        "unassessed",
        "failed",
        "timeouts",
        "outputLimited",
        "memoryLimited",
        "invalidWorkerOutput",
        "scratchAttempted",
        "scratchCompiled",
        "truncated",
    )
    return {field: value[field] for field in fields if field in value}


def _copy_minimal_candidates(
    payload: Mapping[str, Any], result: dict[str, Any]
) -> None:
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        result["candidates"] = [
            _minimal_candidate(card) for card in candidates if isinstance(card, Mapping)
        ]
        return
    candidate = payload.get("candidate")
    if isinstance(candidate, Mapping):
        result["candidate"] = _minimal_candidate(candidate)


def _minimal_candidate(card: Mapping[str, Any]) -> dict[str, Any]:
    check = card.get("check")
    check = check if isinstance(check, Mapping) else {}
    result: dict[str, Any] = {
        "nameFingerprint": card.get("nameFingerprint"),
        "source": _minimal_source(card.get("source")),
        "check": {
            "status": check.get("status"),
            "authority": check.get("authority"),
            "executionBindingLimitation": check.get("executionBindingLimitation"),
            "environmentRef": check.get("environmentRef"),
            "checkRunRef": check.get("checkRunRef"),
            "scratch": _minimal_scratch(check.get("scratch")),
        },
    }
    _copy_minimal_identity_text(
        result["check"], "receiptIdentity", check.get("receiptIdentity"), 128
    )
    _copy_minimal_identity_text(
        result["check"], "sourceReceiptIdentity", check.get("sourceReceiptIdentity"), 128
    )
    return result


def _minimal_source(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {
        field: value[field]
        for field in ("moduleFingerprint", "pathFingerprint", "line")
        if field in value
    }


def _minimal_scratch(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {
        field: value.get(field)
        for field in (
            "status", "environmentRef", "checkRunRef", "authority",
            "receiptIdentity", "sourceReceiptIdentity",
            "executionBindingLimitation",
        )
    }


def _trim_candidate_population(payload: dict[str, Any], maximum: int) -> None:
    candidates = payload["candidates"]
    while not _fits(payload, maximum) and len(candidates) > 1:
        candidates.pop()
        _remove_candidate_omissions(payload, len(candidates))
        _trim_ranking(payload, len(candidates))
        _update_population_coverage(payload, len(candidates))
        omit(payload["omissions"], "/candidates", "projection-byte-limit", 1)


def _remove_candidate_omissions(payload: dict[str, Any], removed_index: int) -> None:
    removed_prefix = f"/candidates/{removed_index}"
    payload["omissions"][:] = [
        row
        for row in payload["omissions"]
        if not str(row.get("pointer", "")).startswith(removed_prefix)
    ]


def _trim_ranking(payload: dict[str, Any], count: int) -> None:
    ranking = payload.get("ranking")
    if not isinstance(ranking, dict):
        return
    contributions = ranking.get("contributions")
    if isinstance(contributions, list):
        ranking["contributions"] = contributions[:count]


def _update_population_coverage(payload: dict[str, Any], count: int) -> None:
    population = payload["coverage"]["candidatePopulation"]
    population["projected"] = count
    population["omitted"] = population["observed"] - count


def _trim_candidate_cards(payload: dict[str, Any], population: bool) -> None:
    cards = payload.get("candidates") or [payload.get("candidate")]
    for index, card in enumerate(cards):
        if not isinstance(card, Mapping) or not isinstance(card.get("check"), dict):
            continue
        pointer = f"/candidates/{index}" if population else "/candidate"
        _trim_candidate_check(card["check"], payload["omissions"], pointer)


def _trim_candidate_check(
    check: dict[str, Any], omissions: list[dict[str, Any]], pointer: str
) -> None:
    for field in _SEMANTIC_ROW_FIELDS:
        _trim_semantic_rows(check, field, omissions, pointer)
    application = check.get("applicationTerm")
    if isinstance(application, str):
        check["applicationTerm"] = truncate_utf8(application, 256)


def _trim_semantic_rows(
    check: dict[str, Any],
    field: str,
    omissions: list[dict[str, Any]],
    pointer: str,
) -> None:
    rows = check.get(field)
    if not isinstance(rows, list) or not rows:
        return
    omit(omissions, f"{pointer}/check/{field}", "projection-byte-limit", len(rows))
    check[field] = []


def _trim_request(payload: dict[str, Any]) -> None:
    request = payload.get("request")
    if not isinstance(request, dict):
        return
    local_context = request.get("localContext")
    if local_context:
        omit(
            payload["omissions"],
            "/request/localContext",
            "projection-byte-limit",
            len(local_context),
        )
        request["localContext"] = []
    for field in ("goal", "module"):
        value = request.get(field)
        if isinstance(value, str):
            request[field] = truncate_utf8(value, 128)


def _fits(payload: Mapping[str, Any], maximum: int) -> bool:
    return len(semantic_projection_bytes(payload)) <= maximum


__all__ = ["finalize_projection", "fit_projection"]
