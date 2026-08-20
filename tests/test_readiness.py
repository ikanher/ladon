from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ladon.readiness import assess_readiness


def _evidence(now: datetime) -> dict[str, object]:
    return {name: {"status": "passed", "timestamp": now.isoformat()} for name in (
        "installedSmoke", "adversarialContract", "resourceGate", "externalOutcome", "platformPosture", "ownerDecision"
    )}


def test_readiness_promotes_only_with_complete_fresh_evidence() -> None:
    now = datetime.now(UTC)
    result = assess_readiness(_evidence(now), now=now)
    assert result["level"] == "release-qualified"


def test_readiness_demotes_stale_evidence() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now - timedelta(days=2))
    result = assess_readiness(evidence, now=now)
    assert result["level"] == "experimental"
