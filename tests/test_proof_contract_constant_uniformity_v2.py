"""Pure template red tests for quantified Nat constant-uniformity v2."""

from __future__ import annotations

import pytest

TEMPLATE = {
    "familyId": "constant-uniformity",
    "version": "constant-uniformity-v2",
    "direction": "right-to-left",
    "kind": "counterexample",
}
STRONG = (("c", "exists"), ("s", "forall"), ("x", "forall"))
WEAK = (("s", "forall"), ("c", "exists"), ("x", "forall"))


def body(offset="0"):
    var = lambda identity: {"tag": "var", "id": identity}
    app = lambda symbol, *args: {"tag": "app", "symbol": symbol, "args": list(args)}
    return {"tag": "le", "left": app("M", var("s"), app("F", var("x"))),
            "right": app("mul", var("c"), app("N", app("add", var("s"),
                                                           {"tag": "const", "name": offset}), var("x")))}


def record(ordered_binders, offset="0"):
    tree = body(offset)
    for identity, quantifier in reversed(ordered_binders):
        tree = {"tag": quantifier, "binder": {"id": identity, "name": identity, "domain": "Nat"},
                "body": tree}
    symbols = {
        "M": {"leanName": "AppProbe.M", "leanType": "Nat → Nat → Nat"},
        "N": {"leanName": "AppProbe.N", "leanType": "Nat → Nat → Nat"},
        "F": {"leanName": "AppProbe.F", "leanType": "Nat → Nat"},
        "mul": {"leanName": "Nat.mul", "leanType": "Nat → Nat → Nat"},
        "add": {"leanName": "Nat.add", "leanType": "Nat → Nat → Nat"},
    }
    return {"formula": tree, "symbols": symbols}


def contract(ordered_binders, offset="0", *, allowed=None):
    identities = [identity for identity, _ in ordered_binders]
    if allowed is None:
        allowed = [] if identities.index("c") < identities.index("s") else ["s"]
    permission = {"state": "known", "allowedBinderIds": allowed, "reason": None}
    return {
        "profileId": "norm-scale-v1", "endpointId": "estimate:AppProbe.F",
        "context": {"objectId": "operator:AppProbe.F", "domainId": "domain:Nat",
                    "scaleId": "scale:AppProbe.N", "representationId": "representation:original"},
        "telescope": [{"binderId": identity, "typeId": "Nat", "quantifier": quantifier}
                      for identity, quantifier in ordered_binders],
        "assumptions": [], "conclusionId": "estimate:AppProbe.bound",
        "features": {
            "regularity": {"state": "known", "scaleId": "scale:AppProbe.N",
                           "offset": int(offset), "reason": None},
            "constantDependencies": {"binderId": "c", **permission},
            "witnessDependencies": [{"binderId": "c", **permission}],
        },
    }


def context_slice():
    return {"localContext": [], "complete": True, "status": "extracted",
            "nodes": [{"kind": "application", "premises": [], "closedType": "(∀ (v0 : Nat), True)"}]}


def match(left_rows=STRONG, right_rows=WEAK, *, left_offset="0", right_offset="0", template=TEMPLATE,
          left_record=None, right_record=None, left_contract=None, right_contract=None):
    from ladon._proof_contract_probe_templates import template_result
    return template_result(left_record or record(left_rows, left_offset),
                           right_record or record(right_rows, right_offset),
                           left_contract or contract(left_rows, left_offset),
                           right_contract or contract(right_rows, right_offset), context_slice(), template)


def test_catalog_v2_supports_constant_choice_and_v1_remains_registered_unsupported():
    from ladon._proof_contract_probe_templates import application_probe_profile
    profile = application_probe_profile()
    assert profile["constant-uniformity"] == {"version": "constant-uniformity-v2", "implemented": True}
    legacy = {**TEMPLATE, "version": "constant-uniformity-v1"}
    result = match(template=legacy)
    assert result["status"] == "unsupported"
    assert result["template"] == legacy


def test_discrepancy_goals_retain_each_original_order():
    result = match()
    assert result["status"] == "planned"
    assert result["scope"] == "closed-nat-constant-uniformity-v2"
    assert [goal["goalId"] for goal in result["goals"]] == ["formal-reading", "probe"]
    formal, probe = (goal["goal"] for goal in result["goals"])
    assert "↔" in formal and formal.index("∀") < formal.index("∃")
    assert "Nat.mul" in formal and "Nat.add" in formal
    assert probe.index("∀") < probe.index("∃") < probe.rindex("∀")
    assert "∧" in probe and "¬" in probe


def test_reverse_implication_retains_strong_order():
    reverse = match(template={**TEMPLATE, "direction": "left-to-right", "kind": "implication"})
    assert reverse["status"] == "planned"
    assert reverse["goals"][1]["goal"].index("∃") < reverse["goals"][1]["goal"].index("∀")


def test_matching_weak_control_preserves_both_existentials():
    result = match(WEAK, WEAK, template={**TEMPLATE, "kind": "implication"})
    assert result["status"] == "planned"
    assert result["goals"][1]["goal"].count("∃") == 2
    assert result["goals"][1]["goal"].count("∀") >= 4


def change_witness_binder(record_value, contract_value):
    contract_value["features"]["witnessDependencies"][0]["binderId"] = "s"


def change_telescope(record_value, contract_value):
    contract_value["telescope"][0], contract_value["telescope"][1] = (
        contract_value["telescope"][1], contract_value["telescope"][0])


def change_permission(record_value, contract_value):
    contract_value["features"]["constantDependencies"]["allowedBinderIds"] = []


def change_offset(record_value, contract_value):
    contract_value["features"]["regularity"]["offset"] = 1


def change_anchor(record_value, contract_value):
    record_value["formula"]["body"]["body"]["body"]["right"]["args"][0] = {"tag": "var", "id": "x"}


@pytest.mark.parametrize("mutation", [change_witness_binder, change_telescope, change_permission,
                                      change_offset, change_anchor])
def test_recognized_metadata_conflicts_reject(mutation):
    left_record, right_record = record(STRONG), record(WEAK)
    left_contract, right_contract = contract(STRONG), contract(WEAK)
    mutation(right_record, right_contract)
    with pytest.raises(ValueError):
        match(left_record=left_record, right_record=right_record,
              left_contract=left_contract, right_contract=right_contract)


def unsupported_symbol(record_value, contract_value):
    record_value["symbols"]["mul"]["leanName"] = "Nat.add"


def unsupported_nonconstant(record_value, contract_value):
    record_value["formula"]["body"]["body"]["body"]["right"]["args"][0] = {
        "tag": "app", "symbol": "M", "args": [{"tag": "var", "id": "s"}, {"tag": "var", "id": "x"}]}


def unsupported_extra_witness(record_value, contract_value):
    record_value["formula"] = {"tag": "exists", "binder": {"id": "d", "name": "d", "domain": "Nat"},
                               "body": record_value["formula"]}


@pytest.mark.parametrize("mutation", [unsupported_symbol, unsupported_nonconstant, unsupported_extra_witness])
def test_unmodeled_formula_shapes_remain_unsupported(mutation):
    left_record, right_record = record(STRONG), record(WEAK)
    mutation(right_record, contract(WEAK))
    result = match(left_record=left_record, right_record=right_record)
    assert result["status"] == "unsupported"
    assert result["goals"] == []


def test_unknown_versions_and_extra_template_fields_reject():
    from ladon._proof_contract_probe_templates import validate_template
    for template in ({**TEMPLATE, "version": "constant-uniformity-v3"},
                     {**TEMPLATE, "extra": True}):
        with pytest.raises(ValueError):
            validate_template(template)
