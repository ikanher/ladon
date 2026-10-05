from __future__ import annotations

import pytest

from ladon.evidence_receipt import build_evidence_receipt, project_evidence_receipt


def _accepted(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "subject": {
            "module": "Main",
            "candidate": "Main.proof",
            "goal": "True",
            "localContext": [],
        },
        "execution_binding": "explicit-pinned",
        "observation_state": "live",
        "operation_outcome": "accepted",
        "authority_basis": "elaborator-check",
        "analysis_completeness": "complete",
        "environment_match": "exact",
        "environment_ref": "sha256:" + "a" * 64,
        "check_run_ref": "check:" + "b" * 64,
    }
    values.update(overrides)
    return values


def test_accepted_receipt_binds_exact_subject_environment_and_check() -> None:
    receipt = build_evidence_receipt(**_accepted())  # type: ignore[arg-type]
    assert receipt["authorityBasis"] == "elaborator-check"
    assert receipt["environmentRef"] == "sha256:" + "a" * 64
    assert receipt["checkRunRef"] == "check:" + "b" * 64


@pytest.mark.parametrize(
    "overrides",
    [
        {"authority_basis": "made-up-authority"},
        {"authority_basis": "producer-assertion"},
        {"environment_ref": None},
        {"check_run_ref": None},
        {"subject": {"candidate": "Main.proof"}},
    ],
)
def test_receipt_rejects_unregistered_or_unattributed_authority(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        build_evidence_receipt(**_accepted(**overrides))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("projection", "state"),
    [("sqlite-row", "stored"), ("dossier", "stored"), ("aggregate", "derived"),
     ("json-renderer", "live"), ("text-renderer", "live"), ("canonical-artifact", "live")],
)
def test_receipt_projection_preserves_binding_and_independent_dimensions(
    projection: str, state: str,
) -> None:
    original = build_evidence_receipt(**_accepted(source_freshness="stale"))
    projected = project_evidence_receipt(original, projection_kind=projection)

    assert original["observationState"] == "live"
    assert projected["observationState"] == state
    expected = {**original, "observationState": state, "receiptIdentity": projected["receiptIdentity"]}
    assert projected == expected
    projected["subject"]["candidate"] = "modified"
    assert original["subject"]["candidate"] == "Main.proof"


def test_receipt_reload_is_idempotent_and_rejects_tampering() -> None:
    original = build_evidence_receipt(**_accepted())
    stored = project_evidence_receipt(original, projection_kind="sqlite-row")
    assert project_evidence_receipt(stored, projection_kind="sqlite-row") == stored
    original["environmentMatch"] = "unknown"
    with pytest.raises(ValueError):
        project_evidence_receipt(original, projection_kind="dossier")
    with pytest.raises(ValueError, match="projection"):
        project_evidence_receipt(stored, projection_kind="unregistered")


def test_reader_can_weaken_binding_and_add_limitations_without_changing_source() -> None:
    original = build_evidence_receipt(**_accepted(limitations=['original limitation']))
    projected = project_evidence_receipt(
        original, projection_kind='sqlite-row', execution_binding='none',
        limitations=['missing recorded context'],
    )
    assert projected['executionBinding'] == 'none'
    assert projected['observationState'] == 'stored'
    assert projected['limitations'] == ['missing recorded context', 'original limitation']
    assert original['executionBinding'] == 'explicit-pinned'
    assert original['limitations'] == ['original limitation']
    assert project_evidence_receipt(projected, projection_kind='sqlite-row') == projected


@pytest.mark.parametrize(('parent', 'child'), [
    ('none', 'ambient-observed'), ('ambient-observed', 'explicit-pinned'), ('explicit-pinned', 'unknown'),
])
def test_reader_binding_override_cannot_escalate_or_invent_binding(parent: str, child: str) -> None:
    original = build_evidence_receipt(**_accepted(execution_binding=parent, observation_state='stored'))
    with pytest.raises(ValueError):
        project_evidence_receipt(original, projection_kind='sqlite-row', execution_binding=child)
