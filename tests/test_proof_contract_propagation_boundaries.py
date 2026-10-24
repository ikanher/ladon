"""Additional isolated regressions for root review findings."""

from __future__ import annotations

from copy import deepcopy

import pytest
from support.proofir_v3_native import ENVIRONMENT, envelope, ref
from test_proof_contract_propagation import (
    _contract,
    _derivation,
    _interface,
    _run,
    _scope,
    _step,
)

from ladon.proof_contract_propagation import propagate_contracts
from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proofir_v3 import validate_envelope


def _binding(step, *, output="out", rule="identity", parameters=None):
    return {
        "stepRef": step["stepRef"],
        "ruleRef": step["ruleRef"],
        "profileDigest": PROFILE_DIGEST,
        "ruleId": rule,
        "arity": len(step["premiseRefs"]),
        "outputInterfaceId": output,
        "parameters": parameters or {},
        "evidenceRefs": [step["checkRunRef"]],
    }


def _anchored_contract(
    contract_id="anchored",
    *,
    endpoint="estimate:f",
    object_id="operator:f",
    domain="domain:X",
    scale="scale:N",
):
    source = _contract(
        contract_id, endpoint=endpoint, object_id=object_id, domain=domain, scale=scale
    )
    payload = deepcopy(source["payload"])
    record = payload["record"]
    record["telescope"].append({"binderId": "w", "typeId": "Nat", "quantifier": "exists"})
    record["features"]["constantDependencies"] = {
        "state": "known",
        "allowedBinderIds": ["u"],
        "reason": None,
        "binderId": "w",
    }
    record["features"]["witnessDependencies"] = [
        {"binderId": "w", "state": "known", "allowedBinderIds": ["u"], "reason": None}
    ]
    artifact = envelope("proofir.contract", payload, source["subjectRefs"], environment=ENVIRONMENT)
    return validate_envelope(artifact).to_dict()


def test_same_contract_local_id_does_not_join_a_different_artifact_interface():
    first = _contract("same", source_map_id="source:first")
    other = _contract("same", source_map_id="source:other")
    graph = _derivation([_step("unused", ["statement:x"], "statement:same")])
    result = propagate_contracts(
        graph,
        [first, other],
        goal_ref=ref("statement", "statement:same"),
        rule_bindings=[],
        endpoint_interfaces=[_interface("first-interface", contract=first)],
        scope_bindings=[_scope(other, statement="statement:same")],
    )
    assert not next(
        row["contracts"]
        for row in result["frontiers"]
        if row["statementRef"] == ref("statement", "statement:same")
    )
    assert result["status"] == "partial"
    assert any(row["code"] == "unsupported-source-scope-transport" for row in result["residuals"])


def test_derived_route_uses_its_declared_output_interface_for_next_step():
    source = _contract("seed")
    first = _step("first", ["statement:seed"], "statement:mid")
    second = _step("second", ["statement:mid"], "statement:goal")
    graph = _derivation([first, second])
    source_interface = _interface("source-interface", contract=source)
    stage = _interface("stage-interface")
    goal = _interface("goal-interface")
    result = _run(
        graph,
        [source],
        goal="statement:goal",
        bindings=[
            _binding(first, output="stage-interface"),
            _binding(second, output="goal-interface"),
        ],
        interfaces=[source_interface, stage, goal],
        scopes=[_scope(source, statement="statement:seed")],
    )
    route = next(
        row["contracts"][0]["routeWitness"]
        for row in result["frontiers"]
        if row["statementRef"] == ref("statement", "statement:goal")
    )
    assert route["interfaceId"] == "goal-interface"
    parent = next(
        row["routeWitness"]
        for row in result["witnesses"]
        if row["witnessRef"] == route["parentWitnessRefs"][0]
    )
    assert parent["interfaceId"] == "stage-interface"


def test_identity_cannot_change_the_contract_interface():
    source = _contract("identity")
    step = _step("identity", ["statement:identity"], "statement:goal")
    wrong = _interface(
        "out", endpoint="estimate:other", operator="operator:f", object_id="operator:f"
    )
    result = _run(
        _derivation([step]),
        [source],
        goal="statement:goal",
        bindings=[_binding(step)],
        interfaces=[_interface("in", contract=source), wrong],
        scopes=[_scope(source, statement="statement:identity")],
    )
    assert not next(
        row["contracts"]
        for row in result["frontiers"]
        if row["statementRef"] == ref("statement", "statement:goal")
    )
    assert any(row["code"] == "incompatible-identity-interface" for row in result["residuals"])


def test_closed_wrapper_rejects_unrecognized_fields():
    source = _contract("closed")
    graph = _derivation([_step("unused", ["statement:x"], "statement:closed")])
    with pytest.raises(ValueError, match="exactly"):
        propagate_contracts(
            graph,
            [source],
            goal_ref=ref("statement", "statement:closed"),
            rule_bindings=[],
            endpoint_interfaces=[{**_interface("in", contract=source), "guess": True}],
            scope_bindings=[_scope(source, statement="statement:closed")],
        )


@pytest.mark.parametrize(
    "mutate, message",
    [
        ("binding-evidence", "exact step check run"),
        ("local-context", "owned reference"),
        ("substitution-kind", "owned reference"),
    ],
)
def test_wrapper_references_are_owned_typed_and_step_bound(mutate, message):
    source = _contract("refs")
    step = _step("refs", ["statement:refs"], "statement:goal")
    binding = _binding(step)
    scope = _scope(source, statement="statement:refs")
    if mutate == "binding-evidence":
        binding["evidenceRefs"] = [ref("check-run", "check:interface")]
    elif mutate == "local-context":
        scope["localContextRef"] = ref("local-context", "context:foreign")
    else:
        scope["substitutionRefs"] = [ref("check-run", "check:source")]
    with pytest.raises(ValueError, match=message):
        _run(
            _derivation([step]),
            [source],
            goal="statement:goal",
            bindings=[binding],
            interfaces=[_interface("out"), _interface("in", contract=source)],
            scopes=[scope],
        )


def test_expired_deadline_reports_partial_coverage():
    graph = _derivation([_step("unused", ["statement:x"], "statement:goal")])
    result = _run(
        graph,
        [],
        goal="statement:goal",
        bindings=[],
        interfaces=[],
        scopes=[],
        bounds={"deadlineUtc": "2000-01-01T00:00:00Z"},
    )
    assert result["status"] == "partial"
    assert result["complete"] is False
    assert result["coverage"]["pending"]


def test_graph_reference_cap_is_enforced():
    graph = _derivation([_step("unused", ["statement:x"], "statement:goal")])
    result = _run(
        graph,
        [],
        goal="statement:goal",
        bindings=[],
        interfaces=[],
        scopes=[],
        bounds={"maxGraphReferences": 1},
    )
    assert result["status"] == "partial"
    assert result["residuals"][0]["code"] == "graph-reference-cap"


def test_output_size_cap_returns_a_bounded_partial_envelope():
    graph = _derivation([_step("unused", ["statement:x"], "statement:goal")])
    result = _run(
        graph,
        [],
        goal="statement:goal",
        bindings=[],
        interfaces=[],
        scopes=[],
        bounds={"maxOutputBytes": 1024},
    )
    assert result["status"] == "partial"
    assert result["residuals"][0]["code"] == "output-size-cap"
    assert len(str(result).encode()) <= 1024


def test_composition_of_explicit_anchored_choice_stays_residual():
    left = _anchored_contract()
    right = _anchored_contract(
        "right", endpoint="estimate:g", object_id="operator:g", domain="domain:Y", scale="scale:M"
    )
    step = _step("compose", ["statement:left", "statement:right"], "statement:goal")
    interfaces = [
        _interface(
            "left",
            endpoint="estimate:f",
            operator="operator:f",
            object_id="operator:f",
            input_type="type:X",
            output_type="type:Y",
            input_scale="scale:N",
            output_scale="scale:M",
            input_norm="norm:N",
            output_norm="norm:M",
            contract=left,
        ),
        _interface(
            "right",
            endpoint="estimate:g",
            operator="operator:g",
            object_id="operator:g",
            domain="domain:Y",
            input_type="type:Y",
            output_type="type:Z",
            input_scale="scale:M",
            output_scale="scale:P",
            input_norm="norm:M",
            output_norm="norm:P",
            contract=right,
        ),
        _interface(
            "out",
            endpoint="estimate:composite",
            operator="operator:composite",
            object_id="operator:composite",
            domain="domain:X",
            input_type="type:X",
            output_type="type:Z",
            input_scale="scale:N",
            output_scale="scale:P",
            input_norm="norm:N",
            output_norm="norm:P",
        ),
    ]
    left_scope = _scope(left, statement="statement:left")
    right_scope = _scope(right, statement="statement:right")
    left_scope["binderMap"].append({"fromBinderId": "w", "toBinderId": "w"})
    right_scope["binderMap"].append({"fromBinderId": "w", "toBinderId": "w"})
    result = _run(
        _derivation([step]),
        [left, right],
        goal="statement:goal",
        bindings=[
            _binding(
                step,
                output="out",
                rule="compose",
                parameters={"compositeOperatorId": "operator:composite"},
            )
        ],
        interfaces=interfaces,
        scopes=[left_scope, right_scope],
    )
    assert not next(
        row["contracts"]
        for row in result["frontiers"]
        if row["statementRef"] == ref("statement", "statement:goal")
    )
    assert any(
        row["code"] == "unsupported-anchored-choice-transport" for row in result["residuals"]
    )
