"""Executable contract for the proposed task 1.1 API (expected red pre-implementation)."""
from __future__ import annotations

from copy import deepcopy

import pytest

from ladon.proof_contract_obligations import (
    BackwardTransformRequest,
    transform_backward_sufficient,
)
from ladon.proof_contract_rules import PROFILE, PROFILE_DIGEST
from ladon.proof_contracts import validate_contract


def contract(*, offset=4, permissions=("b0",), state="known", scale="scale:norm"):
    return {
        "profileId": "norm-scale-v1",
        "endpointId": "estimate:endpoint",
        "context": {
            "objectId": "operator:composite", "domainId": "domain:nat",
            "scaleId": scale, "representationId": "representation:original",
        },
        "telescope": [
            {"binderId": "b0", "typeId": "type:nat", "quantifier": "forall"},
            {"binderId": "w", "typeId": "type:witness", "quantifier": "exists"},
        ],
        "assumptions": [{"predicateId": "assumption:admitted"}],
        "conclusionId": "conclusion:desired",
        "features": {
            "regularity": {"state": "known", "scaleId": scale, "offset": offset, "reason": None},
            "constantDependencies": {
                "state": state,
                "allowedBinderIds": list(permissions) if state == "known" else None,
                "reason": None if state == "known" else "fixture-unknown",
            },
            "witnessDependencies": [{
                "binderId": "w", "state": state,
                "allowedBinderIds": list(permissions) if state == "known" else None,
                "reason": None if state == "known" else "fixture-unknown",
            }],
        },
    }


def iface(identity, *, input_type="type:nat", output_type="type:nat",
          input_scale="scale:norm", output_scale="scale:norm",
          input_norm="norm:n", output_norm="norm:n", object_id="operator:composite"):
    return {
        "interfaceId": identity, "endpointId": "estimate:endpoint",
        "operatorId": object_id, "objectId": object_id, "domainId": "domain:nat",
        "representationId": "representation:original", "inputTypeId": input_type,
        "outputTypeId": output_type, "inputScaleId": input_scale,
        "outputScaleId": output_scale, "inputNormId": input_norm,
        "outputNormId": output_norm, "conclusionId": "conclusion:desired",
        "evidenceRefs": ["check-run:interface:" + identity],
    }


def rule(rule_id):
    return {
        "ruleId": rule_id, "ruleRef": "attributed-application:rule:" + rule_id,
        "ruleDeclaration": PROFILE["rules"].get(rule_id, "fake declaration"),
        "profileDigest": PROFILE_DIGEST, "attributionStatus": "unverified",
        "evidenceRefs": ["attributed-evidence:rule:" + rule_id],
    }


def request(desired, rule_id, premise_interfaces, output=None, *, evidence=None,
            parameters=None, choices=None, bounds=None):
    return BackwardTransformRequest(
        desired_contract=desired,
        rule_evidence=evidence or rule(rule_id),
        premise_interfaces=premise_interfaces,
        output_interface=output or iface("out"),
        parameters=parameters or {}, choices=choices or {}, bounds=bounds or {},
    )


def branch(result, index=0):
    return result["branches"][index]


def requirements(result, index=0):
    return branch(result, index)["requirements"]


def assert_requirement_interface(requirement, interface):
    record = requirement["contractRecord"]
    assert record["context"] == {
        "objectId": interface["objectId"], "domainId": interface["domainId"],
        "scaleId": interface["inputScaleId"],
        "representationId": interface["representationId"],
    }


def _assert_identity_header(result):
    assert result["status"] == "generated"
    assert result["authority"] == "conditional-template"
    assert result["checkerAuthority"] == "none"
    assert "source-binding-unchecked" in result["limitations"]
    assert "evidence-binding-unchecked" in result["limitations"]
    assert result["necessity"] == "not-claimed"
    assert result["profileDigest"] == PROFILE_DIGEST
    assert result["ruleRef"] == "attributed-application:rule:identity"


def _assert_composition_branch(result, desired, i, split, left, right):
    rows = requirements(result, i)
    assert [row["premiseOrdinal"] for row in rows] == [0, 1]
    assert [row["interfaceId"] for row in rows] == ["left", "right"]
    offsets = [row["contractRecord"]["features"]["regularity"]["offset"] for row in rows]
    assert offsets == split and sum(offsets) == 3
    assert all(row["contractRecord"]["telescope"] == desired["telescope"] for row in rows)
    assert all(row["contractRecord"]["assumptions"] == desired["assumptions"] for row in rows)
    assert_requirement_interface(rows[0], left)
    assert_requirement_interface(rows[1], right)
    allowed = set(desired["features"]["constantDependencies"]["allowedBinderIds"])
    assert all(set(row["contractRecord"]["features"]["constantDependencies"]["allowedBinderIds"])
               <= allowed for row in rows)


def test_identity_is_a_sufficient_rule_preimage_and_preserves_full_scope():
    desired = contract()
    result = transform_backward_sufficient(request(desired, "identity", [iface("in")]))
    _assert_identity_header(result)
    got = requirements(result)[0]["contractRecord"]
    assert validate_contract(got) == desired
    assert got["telescope"] == desired["telescope"]
    assert got["assumptions"] == desired["assumptions"]
    assert got["features"]["witnessDependencies"] == desired["features"]["witnessDependencies"]
    assert_requirement_interface(requirements(result)[0], iface("in"))


def test_weaken_loss_requirement_is_sufficient_without_weakest_claim():
    # A lower loss bound suffices for the requested bound by the admitted theorem.
    # It is not necessary: the exact target offset is another sufficient premise.
    desired = contract(offset=4)
    result = transform_backward_sufficient(request(
        desired, "weaken-loss", [iface("in")],
        parameters={"targetOffset": 4, "nestednessRefs": ["check-run:nested"]},
        choices={"weakenLossOffsets": [2]},
    ))
    assert result["status"] == "generated"
    assert result["necessity"] == "not-claimed"
    assert "weakest" not in result["authority"].lower()
    required = requirements(result)[0]["contractRecord"]
    assert required["features"]["regularity"]["offset"] == 2
    assert required["features"]["regularity"]["offset"] <= desired["features"]["regularity"]["offset"]
    # Offset 4 also satisfies the rule side condition, so offset 2 is not necessary.
    alternative = transform_backward_sufficient(request(
        desired, "weaken-loss", [iface("in")],
        parameters={"targetOffset": 4, "nestednessRefs": ["check-run:nested"]},
        choices={"weakenLossOffsets": [4]},
    ))
    assert requirements(alternative)[0]["contractRecord"]["features"]["regularity"]["offset"] == 4
    assert required["telescope"] == desired["telescope"]
    assert_requirement_interface(requirements(result)[0], iface("in"))


def test_combine_estimates_retains_and_ordered_repeated_premise_occurrences():
    desired = contract(offset=5)
    same = iface("same")
    result = transform_backward_sufficient(request(
        desired, "combine-estimates", [same, same], output=same,
        parameters={"leftEmbeddingRefs": ["check-run:left"],
                    "rightEmbeddingRefs": ["check-run:right"],
                    "nestednessRefs": ["check-run:nested"]},
    ))
    rows = requirements(result)
    assert [row["premiseOrdinal"] for row in rows] == [0, 1]
    assert [row["interfaceId"] for row in rows] == ["same", "same"]
    assert len(rows) == 2  # repeated occurrence is not deduplicated
    assert all(row["contractRecord"]["telescope"] == desired["telescope"] for row in rows)
    assert all(row["contractRecord"]["assumptions"] == desired["assumptions"] for row in rows)
    # Union of premise permissions must fit within the desired allowed dependencies.
    allowed = set(desired["features"]["constantDependencies"]["allowedBinderIds"])
    for row in rows:
        req = row["contractRecord"]
        assert set(req["features"]["constantDependencies"]["allowedBinderIds"]) <= allowed
        assert_requirement_interface(row, same)
        witness = req["features"]["witnessDependencies"][0]
        assert set(witness["allowedBinderIds"]) <= allowed


def test_compose_uses_exact_typed_interfaces_and_ordered_nonnegative_splits():
    desired = contract(offset=3, scale="scale:A")
    left = iface("left", input_type="type:A", output_type="type:B",
                 input_scale="scale:A", output_scale="scale:B",
                 input_norm="norm:A", output_norm="norm:B", object_id="operator:left")
    right = iface("right", input_type="type:B", output_type="type:C",
                  input_scale="scale:B", output_scale="scale:C",
                  input_norm="norm:B", output_norm="norm:C", object_id="operator:right")
    out = iface("out", input_type="type:A", output_type="type:C",
                input_scale="scale:A", output_scale="scale:C",
                input_norm="norm:A", output_norm="norm:C", object_id="operator:composite")
    result = transform_backward_sufficient(request(
        desired, "compose", [left, right], output=out,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[1, 2], [2, 1]]},
    ))
    assert result["status"] == "generated"
    assert len(result["branches"]) == 2
    for i, split in enumerate(([1, 2], [2, 1])):
        _assert_composition_branch(result, desired, i, split, left, right)


def test_compose_type_mismatch_is_residual_not_forged_bridge():
    desired = contract(offset=2, scale="scale:A")
    left = iface("left", input_type="type:A", output_type="type:B",
                 input_scale="scale:A", output_scale="scale:B",
                 input_norm="norm:A", output_norm="norm:B")
    right = iface("right", input_type="type:WRONG", output_type="type:C",
                  input_scale="scale:B", output_scale="scale:C",
                  input_norm="norm:B", output_norm="norm:C")
    out = iface("out", input_type="type:A", output_type="type:C",
                input_scale="scale:A", output_scale="scale:C",
                input_norm="norm:A", output_norm="norm:C")
    result = transform_backward_sufficient(request(
        desired, "compose", [left, right], output=out,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[1, 1]]},
    ))
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert any(row["code"] == "incompatible-compose-interface" for row in result["residuals"])


def _compose_inputs(desired_scale="scale:A", output_scale="scale:C"):
    left = iface("left", input_type="type:A", output_type="type:B",
                 input_scale="scale:A", output_scale="scale:B",
                 input_norm="norm:A", output_norm="norm:B")
    right = iface("right", input_type="type:B", output_type="type:C",
                  input_scale="scale:B", output_scale="scale:C",
                  input_norm="norm:B", output_norm="norm:C")
    output = iface("out", input_type="type:A", output_type="type:C",
                   input_scale="scale:A", output_scale=output_scale,
                   input_norm="norm:A", output_norm="norm:C")
    return contract(offset=2, scale=desired_scale), [left, right], output


def test_compose_rejects_wrong_output_outer_scale():
    desired, inputs, output = _compose_inputs(output_scale="scale:wrong")
    result = transform_backward_sufficient(request(
        desired, "compose", inputs, output=output,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[1, 1]]},
    ))
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert any(row["code"] == "incompatible-compose-interface" for row in result["residuals"])


def test_compose_rejects_desired_output_scale_mismatch():
    desired, inputs, output = _compose_inputs(desired_scale="scale:wrong")
    result = transform_backward_sufficient(request(
        desired, "compose", inputs, output=output,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[1, 1]]},
    ))
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert any(row["code"] == "desired-output-interface-mismatch" for row in result["residuals"])


@pytest.mark.parametrize("split", [[1, 1], [3, 1]])
def test_compose_rejects_nonexact_split_without_nestedness_evidence(split):
    desired = contract(offset=3, scale="scale:A")
    left = iface("left", input_type="type:A", output_type="type:B",
                 input_scale="scale:A", output_scale="scale:B",
                 input_norm="norm:A", output_norm="norm:B")
    right = iface("right", input_type="type:B", output_type="type:C",
                  input_scale="scale:B", output_scale="scale:C",
                  input_norm="norm:B", output_norm="norm:C")
    out = iface("out", input_type="type:A", output_type="type:C",
                input_scale="scale:A", output_scale="scale:C",
                input_norm="norm:A", output_norm="norm:C")
    result = transform_backward_sufficient(request(
        desired, "compose", [left, right], output=out,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [split]},
    ))
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert any(row["code"] == "invalid-compose-loss-split" for row in result["residuals"])


@pytest.mark.parametrize("rule_id", ["arbitrary-implication", "unregistered-rule"])
def test_one_way_implication_is_not_reversed_without_admitted_transformer(rule_id):
    result = transform_backward_sufficient(request(contract(), rule_id, [iface("in")]))
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert any(row["code"] in {"unsupported-rule", "unadmitted-rule-evidence"}
               for row in result["residuals"])


def test_unknown_features_and_unchecked_rule_evidence_remain_residual():
    unknown, inputs, output = _compose_inputs()
    unknown["features"]["constantDependencies"]["state"] = "unknown"
    unknown["features"]["constantDependencies"]["allowedBinderIds"] = None
    unknown["features"]["constantDependencies"]["reason"] = "fixture-unknown"
    unknown["features"]["witnessDependencies"][0].update({
        "state": "unknown", "allowedBinderIds": None, "reason": "fixture-unknown",
    })
    result = transform_backward_sufficient(request(
        unknown, "compose", inputs, output=output,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[1, 1]]},
    ))
    assert result["status"] == "residual"
    assert result["branches"] == []
    unchecked = transform_backward_sufficient(request(
        contract(), "identity", [iface("in")], evidence=rule("identity") | {
            "ruleDeclaration": "fake accepted theorem", "attributionStatus": "accepted",
        }
    ))
    assert unchecked["status"] == "residual"
    assert unchecked["branches"] == []
    assert any(row["code"] == "rule-declaration-mismatch" for row in unchecked["residuals"])


def test_attributed_refs_do_not_claim_proof_or_source_authority():
    result = transform_backward_sufficient(request(contract(), "identity", [iface("in")]))
    assert result["authority"] == "conditional-template"
    assert result["checkerAuthority"] == "none"
    assert "source-binding-unchecked" in result["limitations"]
    assert "evidence-binding-unchecked" in result["limitations"]
    assert all(ref.startswith("attributed-") for ref in result["evidenceRefs"])


def test_compose_branch_cap_has_finite_output_and_explicit_pending_count():
    desired, (left, right), out = _compose_inputs()
    desired["features"]["regularity"]["offset"] = 3
    result = transform_backward_sufficient(request(
        desired, "compose", [left, right], output=out,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[0, 3], [1, 2], [2, 1], [3, 0]]},
        bounds={"maxBranches": 2},
    ))
    assert result["status"] == "budget-exhausted"
    assert len(result["branches"]) <= 2
    assert result["coverage"]["branchLimit"] == 2
    assert result["coverage"]["pendingSplitCount"] == 2


def test_bool_integer_and_branch_choice_bounds_are_closed_and_input_safe():
    with pytest.raises((TypeError, ValueError)):
        transform_backward_sufficient(request(contract(offset=True), "identity", [iface("in")]))
    with pytest.raises((TypeError, ValueError)):
        transform_backward_sufficient(request(
            contract(), "identity", [iface("in")], bounds={"maxBranches": True}
        ))
    with pytest.raises((TypeError, ValueError)):
        transform_backward_sufficient(request(
            contract(), "weaken-loss", [iface("in")],
            parameters={"targetOffset": True, "nestednessRefs": ["attributed:nested"]},
        ))
    bool_desired, bool_inputs, bool_output = _compose_inputs()
    with pytest.raises((TypeError, ValueError)):
        transform_backward_sufficient(request(
            bool_desired, "compose", bool_inputs, output=bool_output,
            parameters={"compositeOperatorId": "operator:composite"},
            choices={"lossSplits": [[True, 1]]},
        ))
    desired, (left, right), out = _compose_inputs()
    desired["features"]["regularity"]["offset"] = 3
    result = transform_backward_sufficient(request(
        desired, "compose", [left, right], output=out,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[0, 3], [1, 2], [2, 1]]},
        bounds={"maxBranches": 2},
    ))
    assert len(result["branches"]) <= 2
    assert result["coverage"]["pendingSplitCount"] == 1
    # Output and later caller mutation have independent ownership.
    original_telescope = deepcopy(result["branches"][0]["requirements"][0]["contractRecord"]["telescope"])
    desired["telescope"][0]["binderId"] = "changed-after-call"
    left["interfaceId"] = "changed-after-call"
    assert result["branches"][0]["requirements"][0]["contractRecord"]["telescope"] == original_telescope
    assert result["branches"][0]["requirements"][0]["interfaceId"] == "left"

    class CopyGuard(dict):
        def __deepcopy__(self, _memo):
            raise AssertionError("input record was copied before occurrence-cap preflight")

    over_cap = [CopyGuard(iface("first")), CopyGuard(iface("second"))]
    with pytest.raises(ValueError):
        transform_backward_sufficient(request(
            contract(), "combine-estimates", over_cap,
            parameters={"leftEmbeddingRefs": ["attributed:left"],
                        "rightEmbeddingRefs": ["attributed:right"],
                        "nestednessRefs": ["attributed:nested"]},
            bounds={"maxPremiseOccurrences": 1},
        ))


def test_anchored_compose_choice_stays_residual():
    desired, inputs, out = _compose_inputs()
    desired["features"]["constantDependencies"]["binderId"] = "w"
    result = transform_backward_sufficient(request(
        desired, "compose", inputs, output=out,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[1, 1]]},
    ))
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert any(row["code"] == "unsupported-anchored-choice-transport" for row in result["residuals"])
