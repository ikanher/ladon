"""Dependent domains may use earlier identities, never future or escaped ones."""

import pytest

from ladon.correspondence_interpretation import lower_formula


def quantifier(tag, identity, domain, body):
    return {"tag": tag, "binder": {"id": identity, "name": identity, "domain": domain},
            "body": body}


TRUE = {"tag": "const", "name": "True"}


def test_future_domain_identity_is_rejected_before_lean_elaboration():
    formula = quantifier("forall", "x", "Fin y", quantifier("forall", "y", "Nat", TRUE))
    with pytest.raises(ValueError, match="domain.*scope"):
        lower_formula(formula, {})


def test_escaped_domain_witness_is_rejected():
    formula = {"tag": "and", "items": [quantifier("exists", "k", "Nat", TRUE),
               quantifier("forall", "x", "Fin k", TRUE)]}
    with pytest.raises(ValueError, match="domain.*scope"):
        lower_formula(formula, {})


def test_qualified_scoped_identity_is_substituted_as_a_single_token():
    formula = quantifier("forall", "a.n", "Nat", quantifier("forall", "x", "Fin a.n", TRUE))
    assert "Fin v0" in lower_formula(formula, {})
    assert "Fin a.n" not in lower_formula(formula, {})


def test_free_type_name_cannot_capture_generated_formula_binder():
    formula = quantifier("forall", "n", "Nat", quantifier("forall", "x", "v0", TRUE))
    assert "_root_.v0" in lower_formula(formula, {})
