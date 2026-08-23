"""Deterministic byte-budget fitting for semantic-result projections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.semantic_projection_core import (
    SemanticProjectionError,
    identity,
    omit,
    semantic_projection_bytes,
    truncate_utf8,
)

_SEMANTIC_ROW_FIELDS = ("substitutions", "residualPremises", "dischargedHypotheses")


def finalize_projection(payload: dict[str, Any], maximum: int) -> dict[str, Any]:
    """Fit, identify, and enforce one projection's public byte cap."""

    fit_projection(payload, maximum - 128)
    payload["projection"]["projectionIdentity"] = identity(payload)
    size = len(semantic_projection_bytes(payload))
    if size > maximum:
        raise SemanticProjectionError(
            f"semantic {payload['operation']} projection exceeds its {maximum}-byte cap"
        )
    return payload


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
