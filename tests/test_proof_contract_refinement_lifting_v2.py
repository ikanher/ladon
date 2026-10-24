"""An incomplete lift stays unresolved and retains its abstract witness."""

import pytest

from ladon.proof_contract_refinement import classify_lift_result


def _witness():
    return {"id": "w-1", "status": "abstract-countermodel", "assignment": {"x": "1/2"}}


def test_incomplete_lift_preserves_witness_and_does_not_refute_original_claim():
    witness = _witness()
    attempt = {
        "status": "search-incomplete",
        "reason": "deadline-exhausted",
        "evidence": "lift-attempt-1",
    }

    result = classify_lift_result(witness, attempt)

    assert result == {
        "witnessId": "w-1",
        "abstractWitness": witness,
        "liftAttempt": attempt,
        "status": "unsupported",
        "originalClaimRefuted": False,
        "spuriousnessEvidence": None,
        "openObligation": "checked-realization-or-incompatibility",
    }


def test_unverified_incompatibility_cannot_be_called_spurious():
    with pytest.raises(ValueError, match="unsupported lift result"):
        classify_lift_result(_witness(), {"status": "incompatible", "evidence": "reviewer-label"})
