"""Bounded refinement findings retain witness evidence and authority limits."""

import pytest


def _witness():
    return {
        "id": "w-1",
        "status": "abstract-countermodel",
        "assignment": {"x": "1/2"},
    }


def test_incomplete_lift_preserves_the_abstract_witness_and_attempt():
    from ladon.proof_contract_refinement import classify_lift_result

    witness = _witness()
    attempt = {
        "status": "search-incomplete",
        "reason": "deadline-exhausted",
        "evidence": "lift-attempt-1",
    }

    result = classify_lift_result(witness, attempt)

    assert result["abstractWitness"] == witness
    assert result["liftAttempt"] == attempt
    assert result["status"] == "unsupported"
    assert result["originalClaimRefuted"] is False
    assert result["spuriousnessEvidence"] is None
    assert result["openObligation"] == "checked-realization-or-incompatibility"


def test_unverified_incompatibility_cannot_be_called_spurious():
    from ladon.proof_contract_refinement import classify_lift_result

    with pytest.raises(ValueError, match="unsupported lift result"):
        classify_lift_result(
            _witness(), {"status": "incompatible", "evidence": "reviewer-label"}
        )
