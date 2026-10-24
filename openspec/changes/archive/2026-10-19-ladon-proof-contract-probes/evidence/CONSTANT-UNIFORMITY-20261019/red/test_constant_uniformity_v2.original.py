"""Pure template red tests for quantified Nat constant-uniformity v2."""

from __future__ import annotations

import pytest

TEMPLATE = {
    "familyId": "constant-uniformity",
    "version": "constant-uniformity-v2",
    "direction": "right-to-left",
    "kind": "counterexample",
}


def body(c="c", s="s", x="x", offset="0"):
    var = lambda identity: {"tag": "var", "id": identity}
    app = lambda symbol, *args: {"tag": "app", "symbol": symbol, "args": list(args)}
    return {"tag": "le",
            "left": app("M", var(s), app("F", var(x))),
            "right": app("mul", var(c), app("N", app("add", var(s),
                                                          {"tag": "const", "name": offset}), var(x)))}


def record(quantifiers, offset="0", *, binders=("c", "s", "x")):
    c, s, x = binders
    tree = body(c, s, x, offset)
    for identity, tag in reversed(list(zip(binders, quantifiers))):
        tree = {"tag": tag, "binder": {"id": identity, "name": identity, "domain": "Nat"}, "body": tree}
    symbols = {
        "M": {"leanName": "AppProbe.M", "leanType": "Nat → Nat → Nat"},
        "N": {"leanName": "AppProbe.N", "leanType": "Nat → Nat → Nat"},
        "F": {"leanName": "AppProbe.F", "leanType": "Nat → Nat"},
        "mul": {"leanName": "Nat.mul", "leanType": "Nat → Nat → Nat"},
        "add": {"leanName": "Nat.add", "leanType": "Nat → Nat → Nat"},
    }
    return {"formula": tree, "symbols": symbols}


def contract(quantifiers, offset="0", *, binders=("c", "s", "x"), allowed=None):
    c, s, _x = binders
    if allowed is None:
        allowed = [] if quantifiers[0] == "exists" else [s]
    return {
        "profileId": "norm-scale-v1", "endpointId": "estimate:AppProbe.F",
        "context": {"objectId": "operator:AppProbe.F", "domainId": "domain:Nat",
                    "scaleId": "scale:AppProbe.N", "representationId": "representation:original"},
        "telescope": [{"binderId": identity, "typeId": "Nat", "quantifier": quantifier}
                      for identity, quantifier in zip(binders, quantifiers)],
        "assumptions": [], "conclusionId": "estimate:AppProbe.bound",
        "features": {
            "regularity": {"state": "known", "scaleId": "scale:AppProbe.N",
                           "offset": int(offset), "reason": None},
            "constantDependencies": {"state": "known", "allowedBinderIds": allowed, "reason": None},
            "witnessDependencies": [{"binderId": c, "state": "known",
                                     "allowedBinderIds": allowed, "reason": None}],
        },
    }


def planned(left_q, right_q, *, left_offset="0", right_offset="0", template=TEMPLATE):
    from ladon._proof_contract_probe_templates import template_result
    left_record, right_record = record(left_q, left_offset), record(right_q, right_offset)
    return template_result(left_record, right_record,
                           contract(left_q, left_offset), contract(right_q, right_offset),
                           {"localContext": [], "complete": True, "status": "extracted",
                            "nodes": [{"kind": "application", "premises": [],
                                       "closedType": "(∀ (v0 : Nat), True)"}]}, template)


def test_catalog_v2_supports_constant_choice_and_v1_remains_registered_unsupported():
    from ladon._proof_contract_probe_templates import application_probe_profile
    profile = application_probe_profile()
    assert profile["constant-uniformity"] == {"version": "constant-uniformity-v2", "implemented": True}
    legacy = {**TEMPLATE, "version": "constant-uniformity-v1"}
    result = planned(("forall", "exists", "forall"), ("forall", "exists", "forall"), template=legacy)
    assert result["status"] == "unsupported"
    assert result["template"] == legacy


def test_strong_then_weak_preserves_both_original_quantifier_orders_and_full_goals():
    result = planned(("exists", "forall", "forall"), ("forall", "exists", "forall"))
    assert result["status"] == "planned"
    assert result["scope"] == "closed-nat-constant-uniformity-v2"
    assert [goal["goalId"] for goal in result["goals"]] == ["formal-reading", "probe"]
    formal, probe = (goal["goal"] for goal in result["goals"])
    assert "↔" in formal and formal.index("∃") < formal.index("∀")
    assert "∃" in formal and "Nat.mul" in formal and "Nat.add" in formal
    assert probe.index("∀") < probe.index("∃") < probe.rindex("∀")
    assert "∧" in probe and "¬" in probe


def test_matching_weak_control_and_reverse_direction_are_full_quantified_implications():
    control = planned(("forall", "exists", "forall"), ("forall", "exists", "forall"),
                      template={**TEMPLATE, "kind": "implication"})
    assert control["status"] == "planned"
    assert "→" in control["goals"][1]["goal"]
    assert control["goals"][1]["goal"].count("∃") == 2

    reverse = planned(("exists", "forall", "forall"), ("forall", "exists", "forall"),
                      template={**TEMPLATE, "direction": "left-to-right", "kind": "implication"})
    assert reverse["status"] == "planned"
    assert reverse["goals"][1]["goal"].index("∃") < reverse["goals"][1]["goal"].index("∀")


@pytest.mark.parametrize("mutation", ["binder-id", "telescope-order", "permission", "offset",
                                      "symbol", "nonconstant", "wrong-anchor", "extra-witness"])
def test_recognized_metadata_conflicts_and_unmodeled_witness_shapes_do_not_plan(mutation):
    from ladon._proof_contract_probe_templates import template_result
    strong_record = record(("exists", "forall", "forall"))
    weak_record = record(("forall", "exists", "forall"))
    strong_contract = contract(("exists", "forall", "forall"))
    weak_contract = contract(("forall", "exists", "forall"))
    if mutation == "binder-id":
        strong_contract["features"]["witnessDependencies"][0]["binderId"] = "s"
    elif mutation == "telescope-order":
        weak_contract["telescope"][1], weak_contract["telescope"][2] = (
            weak_contract["telescope"][2], weak_contract["telescope"][1])
    elif mutation == "permission":
        weak_contract["features"]["constantDependencies"]["allowedBinderIds"] = []
    elif mutation == "offset":
        weak_contract["features"]["regularity"]["offset"] = 1
    elif mutation == "symbol":
        weak_record["symbols"]["mul"]["leanName"] = "Nat.add"
    elif mutation == "nonconstant":
        weak_record["formula"]["body"]["body"]["body"]["right"]["args"][0] = {
            "tag": "app", "symbol": "M", "args": [{"tag": "var", "id": "s"}, {"tag": "var", "id": "x"}]}
    elif mutation == "wrong-anchor":
        weak_record["formula"]["body"]["body"]["body"]["right"]["args"][0] = {
            "tag": "var", "id": "x"}
    elif mutation == "extra-witness":
        weak_record["formula"] = {"tag": "exists", "binder": {"id": "d", "name": "d", "domain": "Nat"},
                                  "body": weak_record["formula"]}
    result = template_result(strong_record, weak_record, strong_contract, weak_contract,
                             {"localContext": [], "complete": True, "status": "extracted",
                              "nodes": [{"kind": "application", "premises": [], "closedType": "True"}]},
                             TEMPLATE)
    assert result["status"] in {"unsupported", "rejected"}
    assert result["goals"] == []


def test_unknown_versions_and_extra_template_fields_reject():
    from ladon._proof_contract_probe_templates import validate_template
    for template in ({**TEMPLATE, "version": "constant-uniformity-v3"},
                     {**TEMPLATE, "extra": True}):
        with pytest.raises(ValueError):
            validate_template(template)
