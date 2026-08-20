from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ladon.readiness import assess_readiness


def _evidence(now: datetime) -> dict[str, object]:
    return {
        name: {
            "status": "passed",
            "timestamp": now.isoformat(),
            "command": f"gate {name}",
            "outcome": "passed",
            "candidates": ["fixture.goal"] if name == "externalOutcome" else None,
            "metrics": {"recall": 1.0} if name == "externalOutcome" else None,
        }
        for name in (
            "installedSmoke",
            "adversarialContract",
            "resourceGate",
            "externalOutcome",
            "platformPosture",
            "ownerDecision",
        )
    }


def test_readiness_promotes_only_with_complete_fresh_evidence() -> None:
    now = datetime.now(UTC)
    result = assess_readiness(_evidence(now), now=now)
    assert result["level"] == "release-qualified"


def test_readiness_demotes_stale_evidence() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now - timedelta(days=2))
    result = assess_readiness(evidence, now=now)
    assert result["level"] == "experimental"


def test_readiness_rejects_status_without_command_and_outcome() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now)
    evidence["installedSmoke"] = {"status": "passed", "timestamp": now.isoformat()}
    assert assess_readiness(evidence, now=now)["level"] == "experimental"


def test_readiness_rejects_help_only_external_evidence() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now)
    evidence["externalOutcome"] = {
        "status": "passed",
        "timestamp": now.isoformat(),
        "command": "ladon --help",
        "outcome": "help displayed",
    }
    assert assess_readiness(evidence, now=now)["level"] == "contract-supported"


def test_readiness_rejects_future_naive_and_malformed_age_evidence() -> None:
    now = datetime.now(UTC)
    for timestamp, max_age in (
        ((now + timedelta(days=1)).isoformat(), 86_400),
        (now.replace(tzinfo=None).isoformat(), 86_400),
        (now.isoformat(), "invalid"),
    ):
        evidence = _evidence(now)
        evidence["installedSmoke"]["timestamp"] = timestamp  # type: ignore[index]
        evidence["installedSmoke"]["maxAgeSeconds"] = max_age  # type: ignore[index]
        assert assess_readiness(evidence, now=now)["level"] == "experimental"
