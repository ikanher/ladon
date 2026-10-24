"""A common abstract endpoint never certifies distinct source propositions."""

import pytest
from support.proof_contract_native import contract_artifact

from ladon.proof_contract_artifacts import comparison_artifact
from ladon.proofir_v3 import detached_content_id, validate_envelope, validate_envelope_batch


def distinct_source_comparison():
    left, right = contract_artifact(), contract_artifact()
    right["payload"]["statementRef"] = right["payload"]["conclusionRef"].copy()
    right["artifactId"] = detached_content_id(right)
    comparison = comparison_artifact(left, right, analysis_id="comparison:different-sources")
    return [left, right, comparison]


def test_distinct_sources_only_establish_equality_of_declared_profile_features():
    values = distinct_source_comparison()
    validate_envelope_batch(values)
    result = values[-1]["payload"]["result"]
    assert result["relation"] == "equivalent"
    assert result["authority"] == "profile-structural"
    assert result["mathematicalFalsity"] == "not-established"
    assert values[-1]["payload"]["checkRunRefs"] == []
    assert "source-contract-binding-unchecked" in {r["id"] for r in values[-1]["limitations"]}


def test_comparison_cannot_strip_its_source_binding_limitation():
    comparison = distinct_source_comparison()[-1]
    comparison["limitations"] = []
    comparison["artifactId"] = detached_content_id(comparison)
    with pytest.raises(ValueError, match="source.*binding"):
        validate_envelope(comparison)


def test_profile_comparison_cannot_be_consumed_as_a_formal_derivation_or_source_slice():
    from ladon.correspondence_check import _check_slice
    from ladon.proofir_derivation import evaluate_derivation

    comparison = distinct_source_comparison()[-1]
    goal = {"kind": "statement", "localId": "estimate:bound"}
    evaluated = evaluate_derivation(comparison, goal)
    assert not evaluated.structurally_satisfied
    with pytest.raises(ValueError, match="source-bound extraction"):
        _check_slice(comparison)
