"""Actual statement expressions retain implicit parameters and unsupported forms."""

from pathlib import Path

import pytest

from ladon.proof_contract_production import produce_formal_contract

ROOT = Path(__file__).parent / "fixtures/proof_contract_presentations"


def observe(name):
    return produce_formal_contract(ROOT, "Presentations.lean", "Presentations",
                                   "Presentations." + name)


def test_implicit_binder_identity_is_retained_and_feature_meaning_is_stable():
    implicit, explicit = observe("implicit_index"), observe("explicit_index")
    assert implicit["status"] == explicit["status"] == "extracted"
    assert implicit["contract"] == explicit["contract"]
    assert implicit["observation"]["typeExpr"]["forallE"]["binderInfo"] == "implicit"
    assert explicit["observation"]["typeExpr"]["forallE"]["binderInfo"] == "explicit"


@pytest.mark.parametrize("name", ["nested_witnesses", "unknown_shift"])
def test_unsupported_quantifier_or_scale_retains_the_actual_expression(name):
    result = observe(name)
    assert result["status"] == "unsupported"
    assert result["contract"] is None
    assert result["observation"]["typeExpr"]
    assert result["residuals"]
    assert result["coverage"]["statementFeatures"] == "unsupported"
