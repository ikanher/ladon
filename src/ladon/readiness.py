"""Capability readiness ladder derived from executable evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

READINESS_LEVELS = ("experimental", "contract-supported", "externally-evaluated", "release-qualified")


def assess_readiness(evidence: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Return the highest level whose named evidence is present and fresh."""
    current = now or datetime.now(UTC)
    requirements = {
        "contract-supported": ("installedSmoke", "adversarialContract", "resourceGate"),
        "externally-evaluated": ("installedSmoke", "adversarialContract", "resourceGate", "externalOutcome"),
        "release-qualified": ("installedSmoke", "adversarialContract", "resourceGate", "externalOutcome", "platformPosture", "ownerDecision"),
    }
    level = "experimental"
    reasons: list[str] = []
    for candidate in READINESS_LEVELS[1:]:
        missing = [name for name in requirements[candidate] if not _fresh_pass(evidence.get(name), current)]
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


def _fresh_pass(value: Any, now: datetime) -> bool:
    if not isinstance(value, dict) or value.get("status") != "passed":
        return False
    timestamp = value.get("timestamp")
    if not isinstance(timestamp, str):
        return False
    try:
        observed = datetime.fromisoformat(timestamp)
    except ValueError:
        return False
    return (now - observed).total_seconds() <= float(value.get("maxAgeSeconds", 86_400))


__all__ = ["READINESS_LEVELS", "assess_readiness"]
