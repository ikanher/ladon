"""Boundary regressions identified in the second propagation proposal."""

import pytest
from test_proof_contract_propagation import _contract, _derivation, _interface, _run, _scope, _step
from test_proof_contract_propagation_boundaries import _binding


def _identity_run(*, bounds=None, binding_rule="identity", parameters=None):
    source = _contract("seed")
    step = _step("id", ["statement:seed"], "statement:goal")
    return _run(
        _derivation([step]),
        [source],
        goal="statement:goal",
        bindings=[_binding(step, rule=binding_rule, parameters=parameters)],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[_scope(source, statement="statement:seed")],
        bounds=bounds,
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("maxDepth", 65),
        ("maxGraphReferences", 4097),
        ("maxEvaluatedSteps", 8193),
        ("maxCombinationsPerStep", 4097),
        ("maxFrontierContractsPerStatement", 129),
    ],
)
def test_hard_profile_caps_cannot_be_raised(key, value):
    with pytest.raises(ValueError, match="bound"):
        _identity_run(bounds={key: value})


@pytest.mark.parametrize("rule", ["weaken-loss", "compose"])
def test_required_parameters_raise_value_error(rule):
    with pytest.raises(ValueError, match="parameter"):
        _identity_run(binding_rule=rule)


def test_unbound_leaf_goal_is_not_complete_negative():
    graph = _derivation([_step("unused", ["statement:leaf"], "statement:other")])
    result = _run(graph, [], goal="statement:leaf", bindings=[], interfaces=[], scopes=[])
    assert result["complete"] is False
    assert any(row["code"] == "missing-source-contract" for row in result["residuals"])


def test_equal_contracts_in_different_contexts_keep_the_usable_route():
    from support.proofir_v3_native import ref

    source = _contract("seed")
    step = _step("id", ["statement:seed"], "statement:goal")
    incompatible = _scope(source, statement="statement:seed")
    incompatible["localContextRef"] = ref("local-context", "context:aaa")
    result = _run(
        _derivation([step], [ref("local-context", "context:aaa")]),
        [source],
        goal="statement:goal",
        bindings=[_binding(step)],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[incompatible, _scope(source, statement="statement:seed")],
    )
    goal = next(
        row for row in result["frontiers"] if row["statementRef"]["localId"] == "statement:goal"
    )
    assert goal["contracts"]


def test_inherited_substitution_must_match_application():
    from support.proofir_v3_native import ref

    source = _contract("seed")
    step = _step(
        "id",
        ["statement:seed"],
        "statement:goal",
        substitutions=[{"variable": "u", "termRef": ref("term", "term:new")}],
    )
    scope = _scope(source, statement="statement:seed")
    scope["substitutionRefs"] = [ref("term", "term:old")]
    result = _run(
        _derivation([step], [ref("term", "term:old")]),
        [source],
        goal="statement:goal",
        bindings=[_binding(step)],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[scope],
    )
    goal = next(
        row for row in result["frontiers"] if row["statementRef"]["localId"] == "statement:goal"
    )
    assert not goal["contracts"]
    assert any(row["code"] == "incompatible-substitution" for row in result["residuals"])


def test_preflight_rejects_large_wrapper_before_copy(monkeypatch):
    from ladon import proof_contract_propagation as propagation

    graph = _derivation([_step("id", ["statement:seed"], "statement:goal")])

    def unexpected_validation(*_args, **_kwargs):
        raise AssertionError("native copying preceded wrapper cap")

    monkeypatch.setattr(propagation, "validate_envelope", unexpected_validation)
    result = _run(
        graph,
        [],
        goal="statement:goal",
        bindings=[],
        interfaces=[{"evidenceRefs": [{}] * 4097}],
        scopes=[],
    )
    assert result["status"] == "partial"
    assert result["residuals"][0]["code"] == "graph-reference-cap"


def test_depth_limited_frontier_is_revisited_on_shallower_route():
    source = _contract("seed")
    steps = [
        _step("a-deep", ["statement:middle"], "statement:goal"),
        _step("middle", ["statement:x"], "statement:middle"),
        _step("x", ["statement:seed"], "statement:x"),
        _step("b-shallow", ["statement:x"], "statement:goal"),
    ]
    result = _run(
        _derivation(steps),
        [source],
        goal="statement:goal",
        bindings=[_binding(step) for step in steps],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[_scope(source, statement="statement:seed")],
        bounds={"maxDepth": 2},
    )
    goal = next(
        row for row in result["frontiers"] if row["statementRef"]["localId"] == "statement:goal"
    )
    assert goal["contracts"]
    assert result["complete"] is False
    assert any(row["code"] == "depth-cap" for row in result["coverage"]["pending"])


def test_repeated_shared_proofs_have_linear_witness_storage():
    import json

    source = _contract("seed")
    steps = [_step(f"step:{i}", [f"statement:{i - 1}"] * 2, f"statement:{i}") for i in range(20)]
    result = _run(
        _derivation(steps),
        [source],
        goal="statement:19",
        bindings=[
            _binding(step, rule="compose", parameters={"compositeOperatorId": "operator:f"})
            for step in steps
        ],
        interfaces=[
            _interface(
                "in",
                contract=source,
                output_type="type:X",
                output_scale="scale:N",
                output_norm="norm:N",
            ),
            _interface("out", output_type="type:X", output_scale="scale:N", output_norm="norm:N"),
        ],
        scopes=[_scope(source, statement="statement:-1")],
    )
    assert result["complete"] is True
    assert len(result["witnesses"]) == 21
    assert len(json.dumps(result)) < 160_000
    assert len(result["witnesses"][-1]["routeWitness"].get("premiseOccurrences", [])) <= 2


def test_witness_cap_preserves_known_source_and_omits_derivation():
    result = _identity_run(bounds={"maxWitnessCandidates": 1})
    assert result["complete"] is False
    assert len(result["witnesses"]) == 1
    assert result["coverage"]["counts"]["combinations"] == 0
    assert any(row["code"] == "witness-candidate-cap" for row in result["coverage"]["pending"])
