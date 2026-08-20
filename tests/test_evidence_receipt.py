from __future__ import annotations

import pytest

from ladon.evidence_receipt import build_evidence_receipt


def _accepted(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "subject": {"module": "Main", "candidate": "Main.proof", "goal": "True"},
        "execution_binding": "explicit-pinned",
        "observation_state": "live",
        "operation_outcome": "accepted",
        "authority_basis": "elaborator-check",
        "analysis_completeness": "complete",
        "environment_match": "exact",
        "environment_ref": "sha256:" + "a" * 64,
        "check_run_ref": "check:run",
    }
    values.update(overrides)
    return values


def test_accepted_receipt_binds_exact_subject_environment_and_check() -> None:
    receipt = build_evidence_receipt(**_accepted())  # type: ignore[arg-type]
    assert receipt["authorityBasis"] == "elaborator-check"
    assert receipt["environmentRef"] == "sha256:" + "a" * 64
    assert receipt["checkRunRef"] == "check:run"


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
