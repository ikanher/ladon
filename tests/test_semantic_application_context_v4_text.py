"""Compact views foreground the observed mathematics and disclose omissions."""
from __future__ import annotations

import re

from ladon.proof_search_semantic_cli import render_semantic_candidates
from ladon.semantic_projection_cards import candidate_card


def local(ordinal):
    return {
        "localId": f"local:{ordinal}", "userName": f"x{ordinal}",
        "binderInfo": "implicit", "typeDisplay": "Nat", "typeStructural": "Nat",
        "valueDisplay": "", "valueStructural": "", "dependencies": [],
        "origin": "goal-introduced",
    }


def check():
    return {
        "status": "applicable-with-residuals", "applicationTerm": "Main.step ?h",
        "substitutions": [], "dischargedHypotheses": [],
        "residualPremises": [{"typeDisplay": "P x0", "typeStructural": "app P x0"}],
        "applicationObservationVersion": 4, "semanticProtocol": "ladon-lean-semantic-v4/check-candidate",
        "residualContexts": [{"goalId": "_uniq.1", "localContext": [local(0)]}],
        "selectedDeclaration": {"name": "Main.step", "typeDisplay": "∀ {x : Nat}, P x → Q x", "typeStructural": "opaque-type", "binders": [{**local(0), "origin": "declaration-parameter"}]},
    }


def test_text_shows_residual_local_type_and_selected_parameter_kind():
    result = check()
    text = "\n".join(render_semantic_candidates([{"name": "Main.step", "check": result}], include_projected_evidence=True))
    assert "P x0" in text
    assert re.search(r"x0\s*:\s*Nat", text)
    assert "implicit" in text
    assert result["selectedDeclaration"]["typeDisplay"] in text


def test_bounded_cards_keep_context_ordinal_and_disclose_missing_tail():
    result = check()
    result["residualContexts"][0]["localContext"] = [local(i) for i in range(8)]
    omissions = []
    card = candidate_card("Main.step", result, {}, "llm", {}, omissions, pointer="/candidates/0")
    context = card["check"]["residualContexts"][0]
    assert context["goalId"] == "_uniq.1"
    assert [row["localId"] for row in context["localContext"]] == [f"local:{i}" for i in range(4)]
    assert any(row["pointer"].endswith("/residualContexts/0/localContext") and row["reason"] == "projection-collection-limit" for row in omissions)
    assert card["check"]["selectedDeclaration"]["name"] == "Main.step"
    assert "typeStructural" not in card["check"]["selectedDeclaration"]


def test_legacy_card_does_not_infer_context_from_receipt_or_residual_expression():
    result = check()
    for key in ["applicationObservationVersion", "semanticProtocol", "residualContexts", "selectedDeclaration"]:
        del result[key]
    omissions = []
    card = candidate_card("Main.step", result, {}, "llm", {}, omissions, pointer="/candidates/0")
    assert card["check"].get("residualContexts") is None
    assert card["check"].get("selectedDeclaration") is None
    assert any(row["pointer"].endswith("/residualContexts") and row["reason"] == "canonical-field-unavailable" for row in omissions)
