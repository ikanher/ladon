"""Every generated premise tuple must survive the existing forward semantics."""

from copy import deepcopy

import pytest
from test_proof_contract_backward import _compose_inputs, contract, iface, request

from ladon._contract_propagation_transfer import _transfer
from ladon.proof_contract_obligations import transform_backward_sufficient


def transfer_branch(result, branch, inputs, output, rule, parameters):
    context = {"kind": "local-context", "localId": "context:oracle"}
    step = {"stepRef": {"kind": "derivation-step", "localId": "step:oracle"},
            "localContextRef": context, "substitutions": []}
    rows = [{"contractRecord": requirement["contractRecord"],
             "routeWitness": {"interfaceId": interface["interfaceId"],
                              "localContextRef": context, "substitutionRefs": []}}
            for requirement, interface in zip(branch["requirements"], inputs, strict=True)]
    residuals = []
    forward = _transfer(step, {"ruleId": rule, "parameters": parameters,
                              "outputInterfaceId": output["interfaceId"]},
                        tuple(rows), {r["interfaceId"]: r for r in [*inputs, output]},
                        None, residuals)
    assert not residuals, (result, residuals)
    return forward


@pytest.mark.parametrize("loss", range(6))
@pytest.mark.parametrize("permissions", [[], ["b0"]])
def test_all_selected_composition_splits_reproduce_exact_desired_contract(loss, permissions):
    desired, inputs, output = _compose_inputs()
    desired["features"]["regularity"]["offset"] = loss
    desired["features"]["constantDependencies"]["allowedBinderIds"] = permissions
    desired["features"]["witnessDependencies"][0]["allowedBinderIds"] = permissions
    original = deepcopy(desired)
    parameters = {"compositeOperatorId": "operator:composite"}
    result = transform_backward_sufficient(request(
        desired, "compose", inputs, output=output, parameters=parameters,
        choices={"lossSplits": [[left, loss - left] for left in range(loss + 1)]},
    ))
    assert result["status"] == "generated"
    assert len(result["branches"]) == loss + 1
    for branch in result["branches"]:
        assert transfer_branch(result, branch, inputs, output, "compose", parameters) == desired
    assert desired == original


@pytest.mark.parametrize("rule", ["identity", "weaken-loss", "combine-estimates"])
def test_generated_noncompose_requirements_reproduce_exact_desired_contract(rule):
    desired = contract(offset=4)
    inputs = [iface("input") for _ in range(2 if rule == "combine-estimates" else 1)]
    parameters = {
        "identity": {},
        "weaken-loss": {"targetOffset": 4, "nestednessRefs": ["attributed:nesting"]},
        "combine-estimates": {"leftEmbeddingRefs": ["attributed:left"],
                              "rightEmbeddingRefs": ["attributed:right"],
                              "nestednessRefs": ["attributed:nesting"]},
    }[rule]
    choices = {"weakenLossOffsets": [0, 2, 4]} if rule == "weaken-loss" else {}
    output = iface("out")
    result = transform_backward_sufficient(request(
        desired, rule, inputs, output=output, parameters=parameters, choices=choices,
    ))
    assert result["status"] == "generated"
    for branch in result["branches"]:
        assert transfer_branch(result, branch, inputs, output, rule, parameters) == desired
