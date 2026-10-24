"""Proposed acceptance tests, intentionally red on 0.3.0; no production edits.

The proposed additive findings projection uses statementRelation/methodRelation
with the existing authored judgment values. It must not assert mathematical truth.
"""

import pytest

from probe_runtime import observe


@pytest.fixture(scope="module")
def observed():
    rows = observe()["cases"]
    assert all(row["exitCode"] == 0 for row in rows)
    return {row["id"]: row["stdout"] for row in rows}


def test_statement_mismatch_survives_completed_review(observed):
    result = observed["mismatch-different"]
    assert result["counts"]["reviewedClaims"] == 1
    assert any(item.get("statementRelation") == "mismatch"
               for item in result.get("findings", [])), "Reviewed mismatch disappeared from output"


def test_different_method_survives_aligned_statement(observed):
    result = observed["aligned-different"]
    assert any(item.get("statementRelation") == "aligned"
               and item.get("methodRelation") == "different"
               for item in result.get("findings", [])), "Valid different method disappeared"


def test_same_method_control_does_not_gain_discrepancy(observed):
    result = observed["aligned-same"]
    assert result["counts"]["reviewedClaims"] == 1
    assert not any(item.get("statementRelation") == "mismatch"
                   or item.get("methodRelation") == "different"
                   for item in result.get("findings", []))
