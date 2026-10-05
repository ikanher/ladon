"""Compact artifact-validation observations, separate from theorem dossiers."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ladon.result_manifest import review_currency
from ladon.result_manifest_io import MAX_RESULT_BYTES, canonical_json


def manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    """Summarize an already validated manifest with bounded review observations."""

    reviews, statuses = _review_observations(manifest)
    counts = Counter(row["currency"] for row in reviews)
    result = {
        "schema": "ladon-result-validation-v1",
        "operation": "validate",
        "status": "valid",
        "validationScope": "offline-manifest-integrity",
        "readiness": "experimental",
        "resultId": manifest["resultId"],
        "revision": manifest["revision"],
        "collections": {key: len(manifest[key]) for key in ("claims", "targets", "links", "reviews")},
        "mapping": _mapping_coverage(manifest),
        "canonicalResolution": {
            "status": "not-assessed",
            "unresolvedLinks": len(manifest["links"]),
            "reason": "canonical-evidence-not-loaded",
        },
        "reviewSummary": {
            "current": counts["current"],
            "historical": counts["historical"],
            "correspondenceStatuses": dict(sorted(Counter(statuses).items())),
            "authority": "attributed-review-assertions",
            "reviewerAuthentication": "not-assessed",
        },
        "reviewObservations": reviews[:100],
        "omissions": {"reviewObservations": max(0, len(reviews) - 100)},
        "nonclaims": [
            "Valid means manifest shape, declared content revisions, and internal references only.",
            "Canonical targets remain unresolved; Lean and referenced evidence were not loaded.",
            "Current reviews are attributed assertions, not correspondence or understanding guarantees.",
        ],
    }
    while len(canonical_json(result)) > MAX_RESULT_BYTES - 1:
        result["reviewObservations"].pop()
        result["omissions"]["reviewObservations"] += 1
    return result


def _mapping_coverage(manifest: dict) -> dict:
    components = {(claim["id"], part) for claim in manifest["claims"] for part in claim["components"]}
    linked = {(link["claimId"], part) for link in manifest["links"] for part in link["componentIds"]}
    return {
        "declaredComponents": len(components),
        "linkedComponents": len(linked),
        "unmappedComponents": len(components - linked),
        "inventoryCoverage": manifest["claimInventory"]["coverage"],
        "authority": "producer-declared-mapping",
    }


def _review_observations(manifest: dict) -> tuple[list[dict], list[str]]:
    claims = {row["id"]: row for row in manifest["claims"]}
    targets = {row["id"]: row for row in manifest["targets"]}
    links = {row["id"]: row for row in manifest["links"]}
    current: dict[str, set[str]] = {identifier: set() for identifier in links}
    observations = []
    for review in manifest["reviews"]:
        link = links[review["linkId"]]
        currency = review_currency(review, link, claims[link["claimId"]], targets)
        observations.append({
            "id": review["id"], "linkId": review["linkId"], "currency": currency,
            "reportedStatus": review["status"], "reviewerKind": review["reviewer"]["kind"],
        })
        if currency == "current":
            current[review["linkId"]].add(review["status"])
    return observations, [_correspondence_status(values) for values in current.values()]


def _correspondence_status(values: set[str]) -> str:
    if not values:
        return "not-reviewed"
    if len(values) > 1 or "disputed" in values:
        return "disputed"
    return next(iter(values))
