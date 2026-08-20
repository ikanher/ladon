"""Capability readiness ladder derived from executable evidence."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

READINESS_LEVELS = ("experimental", "contract-supported", "externally-evaluated", "release-qualified")
EVIDENCE_FIELDS = {
    "installedSmoke": ("command", "outcome"),
    "adversarialContract": ("command", "outcome"),
    "resourceGate": ("command", "outcome"),
    "externalOutcome": ("command", "outcome", "candidates", "metrics"),
    "platformPosture": ("command", "outcome"),
    "ownerDecision": ("command", "outcome"),
}


def assess_readiness(evidence: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Return the highest level whose named evidence is present and fresh."""
    current = now or datetime.now(UTC)
    if current.utcoffset() is None:
        current = current.replace(tzinfo=UTC)
    requirements = {
        "contract-supported": ("installedSmoke", "adversarialContract", "resourceGate"),
        "externally-evaluated": ("installedSmoke", "adversarialContract", "resourceGate", "externalOutcome"),
        "release-qualified": ("installedSmoke", "adversarialContract", "resourceGate", "externalOutcome", "platformPosture", "ownerDecision"),
    }
    level = "experimental"
    reasons: list[str] = []
    for candidate in READINESS_LEVELS[1:]:
        missing = [
            name
            for name in requirements[candidate]
            if not _fresh_pass(evidence.get(name), current, EVIDENCE_FIELDS[name])
        ]
        if missing:
            reasons.extend(f"{candidate}: missing or stale {name}" for name in missing)
            break
        level = candidate
    return {
        "schema": "ladon-capability-readiness-v1",
        "level": level,
        "evidence": evidence,
        "reasons": reasons,
        "evaluatedAt": current.isoformat(),
        "nonclaims": ["Readiness is not proof authority and does not grant public distribution rights."],
    }


def _fresh_pass(value: Any, now: datetime, required_fields: tuple[str, ...]) -> bool:
    if not isinstance(value, dict) or value.get("status") != "passed":
        return False
    if any(not value.get(field) for field in required_fields):
        return False
    timestamp = value.get("timestamp")
    if not isinstance(timestamp, str):
        return False
    try:
        observed = datetime.fromisoformat(timestamp)
        max_age = float(value.get("maxAgeSeconds", 86_400))
    except (TypeError, ValueError):
        return False
    if observed.utcoffset() is None or not math.isfinite(max_age) or max_age <= 0:
        return False
    age = (now - observed).total_seconds()
    return 0 <= age <= max_age


__all__ = ["READINESS_LEVELS", "assess_readiness"]
