"""Red integration proposals for bounded conditional contract propagation.

These tests are deliberately isolated from the canonical product test tree.
They exercise validated native derivation and contract artifacts, but their
synthetic contracts do not establish source fidelity or theorem truth.
"""

from __future__ import annotations

import pytest
from support.proofir_v3_native import ENVIRONMENT, envelope, ref

from ladon.proof_contract_propagation import propagate_contracts
from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proofir_v3 import validate_envelope


def _contract(contract_id, *, offset=3, dependencies=("u",), endpoint="estimate:f",
              object_id="operator:f", domain="domain:X", scale="scale:N", source_map_id=None):
    record = {
        "profileId": "norm-scale-v1",
        "endpointId": endpoint,
        "context": {
            "objectId": object_id,
            "domainId": domain,
            "scaleId": scale,
            "representationId": "representation:original",
        },
        "telescope": [{"binderId": "u", "typeId": "Nat", "quantifier": "forall"}],
        "assumptions": [{"predicateId": "input:valid"}],
        "conclusionId": "estimate:bound",
        "features": {
            "regularity": {"state": "known", "scaleId": scale, "offset": offset,
                            "reason": None},
            "constantDependencies": {"state": "known",
                                      "allowedBinderIds": list(dependencies), "reason": None},
            "witnessDependencies": [],
        },
    }
    source_ref = ref("source-map", source_map_id or f"source:{contract_id}")
    statement_ref = ref("statement", f"statement:{contract_id}")
    assumption_refs = [ref("statement", "input:valid")]
    conclusion_ref = ref("statement", "estimate:bound")
    subjects = [ref("contract", contract_id), statement_ref, *assumption_refs,
                conclusion_ref, source_ref]
    artifact = envelope(
        "proofir.contract",
        {
            "contractId": contract_id,
            "profileDigest": PROFILE_DIGEST,
            "record": record,
            "statementRef": statement_ref,
            "assumptionRefs": assumption_refs,
            "conclusionRef": conclusion_ref,
            "sourceMapRefs": [source_ref],
            "checkRunRefs": [],
            "provenance": {
                "mode": "authored", "fidelity": "attributed-unreviewed",
                "completeness": "complete", "checkerAuthority": "none",
                "mathematicalFalsity": "not-established",
            },
            "residuals": [],
        },
        subjects,
        environment=ENVIRONMENT,
    )
    return validate_envelope(artifact).to_dict()


def _derivation(steps, extra_subjects=()):
    subjects = []
    for step in steps:
        subjects.extend(step["premiseRefs"])
        subjects.extend(
            [step["conclusionRef"], step["stepRef"], step["ruleRef"],
             step["localContextRef"], step["checkRunRef"]]
        )
        subjects.extend(row["termRef"] for row in step["substitutions"])
    subjects.extend([ref("check-run", "check:source"),
                     ref("check-run", "check:interface")])
    subjects.extend(extra_subjects)
    unique = {(row["kind"], row["localId"]): row for row in subjects}
    return envelope(
        "proofir.derivation",
        {"derivationId": "derivation:fixture", "acyclic": True, "steps": steps},
        list(unique.values()),
        environment=ENVIRONMENT,
    )


def _cyclic_derivation():
    statements = [ref("statement", name) for name in ("A", "B")]
    steps = [
        _step("cycle-a", ["B"], "A"),
        _step("cycle-b", ["A"], "B"),
    ]
    payload = {
        "derivationId": "derivation:cycle",
        "acyclic": False,
        "recursion": {
            "policy": "declared-strongly-connected-components",
            "components": [{
                "componentId": "scc:ab",
                "semantics": "declared-recursive-fixed-point",
                "statementRefs": statements,
            }],
        },
        "steps": steps,
    }
    subjects = [*statements]
    for step in steps:
        subjects.extend([step["stepRef"], step["ruleRef"], step["localContextRef"],
                         step["checkRunRef"]])
    subjects.extend([ref("check-run", "check:source"), ref("check-run", "check:interface")])
    unique = {(row["kind"], row["localId"]): row for row in subjects}
    return envelope("proofir.derivation", payload, list(unique.values()), environment=ENVIRONMENT)


def _step(name, premises, conclusion, *, context="context:shared", rule=None,
          substitutions=()):
    return {
        "stepRef": ref("derivation-step", f"step:{name}"),
        "kind": "theorem-application",
        "ruleRef": ref("declaration", rule or f"rule:{name}"),
        "premiseRefs": [ref("statement", value) for value in premises],
        "conclusionRef": ref("statement", conclusion),
        "substitutions": list(substitutions),
        "localContextRef": ref("local-context", context),
        "checkRunRef": ref("check-run", f"check:{name}"),
    }


def _external_contract(artifact):
    return {
        "artifactRef": artifact["artifactId"],
        "kind": "contract",
        "localId": artifact["payload"]["contractId"],
    }


def _scope(artifact, *, statement=None, context="context:shared", object_id=None):
    record = artifact["payload"]["record"]
    return {
        "contractRef": _external_contract(artifact),
        "statementRef": ref("statement", statement or artifact["payload"]["statementRef"]["localId"]),
        "localContextRef": ref("local-context", context),
        "objectMap": [{"fromObjectId": record["context"]["objectId"],
                       "toObjectId": object_id or record["context"]["objectId"]}],
        "binderMap": [{"fromBinderId": "u", "toBinderId": "u"}],
        "substitutionRefs": [],
        "evidenceRefs": [ref("check-run", "check:source")],
    }


def _interface(interface_id, *, endpoint="estimate:f", operator="operator:f",
               object_id="operator:f", domain="domain:X", representation="representation:original",
               input_type="type:X", output_type="type:Y", input_scale="scale:N",
               output_scale="scale:M", input_norm="norm:N", output_norm="norm:M",
               conclusion="estimate:bound", contract=None):
    value = {
        "interfaceId": interface_id,
        "endpointId": endpoint,
        "operatorId": operator,
        "objectId": object_id,
        "domainId": domain,
        "representationId": representation,
        "inputTypeId": input_type,
        "outputTypeId": output_type,
        "inputScaleId": input_scale,
        "outputScaleId": output_scale,
        "inputNormId": input_norm,
        "outputNormId": output_norm,
        "conclusionId": conclusion,
        "evidenceRefs": [ref("check-run", "check:interface")],
    }
    if contract is not None:
        value["contractRef"] = _external_contract(contract)
    return value


def _binding(step, *, rule_id="identity", output_interface="out", arity=1,
             parameters=None):
    return {
        "stepRef": step["stepRef"],
        "ruleRef": step["ruleRef"],
        "profileDigest": PROFILE_DIGEST,
        "ruleId": rule_id,
        "arity": arity,
        "outputInterfaceId": output_interface,
        "parameters": parameters or {},
        "evidenceRefs": [step["checkRunRef"]],
    }


def _run(derivation, artifacts, *, goal, bindings, interfaces, scopes, bounds=None):
    return propagate_contracts(
        derivation,
        artifacts,
        goal_ref=ref("statement", goal),
        rule_bindings=bindings,
        endpoint_interfaces=interfaces,
        scope_bindings=scopes,
        bounds=bounds,
    )


def _goal_frontier(result, goal):
    return next(row["contracts"] for row in result["frontiers"]
                if row["statementRef"] == ref("statement", goal))


def _independent_oracle_graph():
    steps = []
    incoming = {f"s{index}": [] for index in range(8)}
    for node in range(3, 8):
        parents = list(range(max(0, node - 3), node))
        assert len(parents) <= 3
        for parent in parents:
            step = _step(f"edge-{parent}-{node}", [f"s{parent}"], f"s{node}")
            steps.append(step)
            incoming[f"s{node}"].append(f"s{parent}")
    return steps, incoming, _derivation(steps)


def _independent_oracle_sources(source_scores):
    return [
        _contract(f"s{index}", offset=loss, dependencies=tuple(sorted(deps)),
                  endpoint="estimate:fixed", object_id="operator:fixed")
        for index, (loss, deps) in enumerate(source_scores)
    ]


def _enumerate_oracle_routes(incoming):
    routes = {f"s{index}": {index} for index in range(3)}
    for node in range(3, 8):
        routes[f"s{node}"] = set().union(
            *(routes[parent] for parent in incoming[f"s{node}"])
        )
    return routes["s7"]


def _oracle_candidate_is_dominated(candidate, other):
    loss, dependencies = candidate
    other_loss, other_dependencies = other
    return (other_loss <= loss and other_dependencies <= dependencies
            and (other_loss < loss or other_dependencies < dependencies))


def _minimal_oracle_frontier(candidates):
    return {
        (loss, tuple(sorted(dependencies)))
        for loss, dependencies in candidates
        if not any(_oracle_candidate_is_dominated((loss, dependencies), other)
                   for other in candidates)
    }


def _oracle_bindings(steps):
    return [_binding(step, output_interface="identity-output") for step in steps]


def _oracle_interfaces(sources, identity_output):
    return [identity_output, *[
        _interface(f"input-{index}", endpoint="estimate:fixed", operator="operator:fixed",
                   object_id="operator:fixed", contract=source)
        for index, source in enumerate(sources)
    ]]


def _oracle_scopes(sources):
    return [_scope(source, statement=f"s{index}") for index, source in enumerate(sources)]


def test_and_application_with_missing_conjunct_keeps_exact_residual_occurrence():
    source_a = _contract("a")
    step = _step("and", ["statement:a", "statement:b"], "statement:goal")
    graph = _derivation([step])
    output_interface = _interface("out", endpoint="estimate:goal", operator="operator:goal",
                                  object_id="operator:goal", input_type="type:X",
                                  output_type="type:Z", output_scale="scale:P",
                                  output_norm="norm:P")
    result = _run(
        graph, [source_a], goal="statement:goal",
        bindings=[_binding(step, rule_id="compose", arity=2,
                           parameters={"compositeOperatorId": "operator:goal"})],
        interfaces=[_interface("in-a", contract=source_a),
                    _interface("in-b", endpoint="estimate:g", operator="operator:g",
                               object_id="operator:g", input_type="type:Y",
                               output_type="type:Z", input_scale="scale:M",
                               output_scale="scale:P", input_norm="norm:M",
                               output_norm="norm:P"), output_interface],
        scopes=[_scope(source_a, statement="statement:a")],
    )

    assert _goal_frontier(result, "statement:goal") == []
    residual = next(row for row in result["residuals"]
                    if row.get("stepRef") == step["stepRef"])
    assert residual["premiseOrdinal"] == 1
    assert result["status"] in {"partial", "complete"}
    assert result["authority"] == "conditional-profile"
    assert result["mathematicalFalsity"] == "not-established"


def test_repeated_premise_occurrences_remain_distinct_in_route_witness():
    source = _contract("self", endpoint="estimate:id", object_id="operator:id")
    substitution = {"variable": "u", "termRef": ref("term", "term:u")}
    step = _step("repeat", ["statement:self", "statement:self"], "statement:goal",
                 substitutions=[substitution])
    graph = _derivation([step])
    in_interface = _interface(
        "in-self", endpoint="estimate:id", operator="operator:id", object_id="operator:id",
        input_type="type:X", output_type="type:X", input_scale="scale:N",
        output_scale="scale:N", input_norm="norm:N", output_norm="norm:N", contract=source,
    )
    output_interface = _interface(
        "out", endpoint="estimate:id-self", operator="operator:id-self",
        object_id="operator:id-self", input_type="type:X", output_type="type:X",
        input_scale="scale:N", output_scale="scale:N", input_norm="norm:N",
        output_norm="norm:N",
    )
    result = _run(
        graph, [source], goal="statement:goal",
        bindings=[_binding(step, rule_id="compose", arity=2,
                           output_interface="out",
                           parameters={"compositeOperatorId": "operator:id-self"})],
        interfaces=[in_interface, output_interface],
        scopes=[_scope(source, statement="statement:self")],
    )
    route = _goal_frontier(result, "statement:goal")[0]["routeWitness"]
    occurrences = route["premiseOccurrences"]
    assert [row["ordinal"] for row in occurrences] == [0, 1]
    assert occurrences[0]["contractRef"] == occurrences[1]["contractRef"]
    assert route["substitutionRefs"] == [ref("term", "term:u")]


def test_or_alternatives_keep_correlated_loss_dependency_tuples():
    route_a = _contract("a", offset=3, dependencies=("u",), endpoint="estimate:goal",
                        object_id="operator:goal")
    route_b = _contract("b", offset=5, dependencies=(), endpoint="estimate:goal",
                        object_id="operator:goal")
    step_a = _step("a", ["statement:a"], "statement:goal")
    step_b = _step("b", ["statement:b"], "statement:goal")
    graph = _derivation([step_b, step_a])
    output = _interface("out", endpoint="estimate:goal", operator="operator:goal",
                        object_id="operator:goal")
    result = _run(
        graph, [route_a, route_b], goal="statement:goal",
        bindings=[_binding(step_a, output_interface="out"),
                  _binding(step_b, output_interface="out")],
        interfaces=[output, _interface("a", endpoint="estimate:goal", operator="operator:goal",
                                      object_id="operator:goal", contract=route_a),
                    _interface("b", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=route_b)],
        scopes=[_scope(route_a, statement="statement:a"),
                _scope(route_b, statement="statement:b")],
    )
    frontier = _goal_frontier(result, "statement:goal")
    assert len(frontier) == 2
    assert {(row["contractRecord"]["features"]["regularity"]["offset"],
             tuple(row["contractRecord"]["features"]["constantDependencies"]["allowedBinderIds"]))
            for row in frontier} == {(3, ("u",)), (5, ())}
    assert result["status"] in {"complete", "partial"}


def test_dominance_reduction_keeps_removed_route_provenance():
    strong = _contract("strong", offset=3, dependencies=(), endpoint="estimate:goal",
                       object_id="operator:goal")
    weak = _contract("weak", offset=5, dependencies=("u",), endpoint="estimate:goal",
                     object_id="operator:goal")
    step_a = _step("strong", ["statement:a"], "statement:goal")
    step_b = _step("weak", ["statement:b"], "statement:goal")
    graph = _derivation([step_a, step_b])
    output = _interface("out", endpoint="estimate:goal", operator="operator:goal",
                        object_id="operator:goal")
    result = _run(
        graph, [strong, weak], goal="statement:goal",
        bindings=[_binding(step_a), _binding(step_b)],
        interfaces=[output, _interface("strong", endpoint="estimate:goal", operator="operator:goal",
                                       object_id="operator:goal", contract=strong),
                    _interface("weak", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=weak)],
        scopes=[_scope(strong, statement="statement:a"), _scope(weak, statement="statement:b")],
    )
    assert len(_goal_frontier(result, "statement:goal")) == 1
    assert result["prunings"]
    assert result["prunings"][0]["removedWitness"]
    assert result["prunings"][0]["dominanceEvidence"]


def test_incompatible_local_context_yields_residual_not_cross_branch_join():
    source = _contract("a")
    step = _step("context", ["statement:a"], "statement:goal", context="context:step")
    graph = _derivation([step], [ref("local-context", "context:other")])
    output = _interface("out")
    result = _run(
        graph, [source], goal="statement:goal", bindings=[_binding(step)],
        interfaces=[output, _interface("in", contract=source)],
        scopes=[_scope(source, statement="statement:a", context="context:other")],
    )
    assert _goal_frontier(result, "statement:goal") == []
    assert any(row.get("stepRef") == step["stepRef"] for row in result["residuals"])


@pytest.mark.parametrize(
    ("right_type", "right_scale", "right_norm", "right_context_scale"),
    [
        ("type:WRONG", "scale:M", "norm:M", "scale:M"),
        ("type:Y", "scale:WRONG", "norm:M", "scale:WRONG"),
        ("type:Y", "scale:M", "norm:WRONG", "scale:M"),
    ],
)
def test_composition_rejects_mismatched_intermediate_type_scale_or_norm(
    right_type, right_scale, right_norm, right_context_scale
):
    left = _contract("left", endpoint="estimate:f", object_id="operator:f")
    right = _contract("right", endpoint="estimate:g", object_id="operator:g",
                      domain="domain:Y", scale=right_context_scale)
    step = _step("compose", ["statement:left", "statement:right"], "statement:goal")
    graph = _derivation([step])
    interfaces = [
        _interface("left", endpoint="estimate:f", operator="operator:f", object_id="operator:f",
                   input_type="type:X", output_type="type:Y", input_scale="scale:N",
                   output_scale="scale:M", input_norm="norm:N", output_norm="norm:M",
                   contract=left),
        _interface("right", endpoint="estimate:g", operator="operator:g", object_id="operator:g",
                   domain="domain:Y",
                   input_type=right_type, output_type="type:Z", input_scale=right_scale,
                   output_scale="scale:P", input_norm=right_norm, output_norm="norm:P",
                   contract=right),
        _interface("out", endpoint="estimate:composite", operator="operator:composite",
                   object_id="operator:composite", input_type="type:X", output_type="type:Z",
                   input_scale="scale:N", output_scale="scale:P", input_norm="norm:N",
                   output_norm="norm:P"),
    ]
    result = _run(
        graph, [left, right], goal="statement:goal",
        bindings=[_binding(step, rule_id="compose", arity=2,
                           parameters={"compositeOperatorId": "operator:composite"})],
        interfaces=interfaces,
        scopes=[_scope(left, statement="statement:left"),
                _scope(right, statement="statement:right")],
    )
    assert _goal_frontier(result, "statement:goal") == []
    assert any(row.get("stepRef") == step["stepRef"] for row in result["residuals"])


def test_sequential_estimate_composition_sums_loss_on_exact_intermediate_interface():
    left = _contract("left", offset=3, endpoint="estimate:f", object_id="operator:f")
    right = _contract("right", offset=5, endpoint="estimate:g", object_id="operator:g",
                      domain="domain:Y", scale="scale:M")
    step = _step("compose-valid", ["statement:left", "statement:right"], "statement:goal")
    graph = _derivation([step])
    interfaces = [
        _interface("left", endpoint="estimate:f", operator="operator:f", object_id="operator:f",
                   input_type="type:X", output_type="type:Y", input_scale="scale:N",
                   output_scale="scale:M", input_norm="norm:N", output_norm="norm:M",
                   contract=left),
        _interface("right", endpoint="estimate:g", operator="operator:g", object_id="operator:g",
                   domain="domain:Y", input_type="type:Y", output_type="type:Z",
                   input_scale="scale:M", output_scale="scale:P", input_norm="norm:M",
                   output_norm="norm:P", contract=right),
        _interface("composite", endpoint="estimate:g-after-f", operator="operator:g-after-f",
                   object_id="operator:g-after-f", domain="domain:X",
                   input_type="type:X", output_type="type:Z", input_scale="scale:N",
                   output_scale="scale:P", input_norm="norm:N", output_norm="norm:P"),
    ]
    result = _run(
        graph, [left, right], goal="statement:goal",
        bindings=[_binding(step, rule_id="compose", arity=2,
                           output_interface="composite",
                           parameters={"compositeOperatorId": "operator:g-after-f"})],
        interfaces=interfaces,
        scopes=[_scope(left, statement="statement:left"),
                _scope(right, statement="statement:right")],
    )
    output = _goal_frontier(result, "statement:goal")[0]["contractRecord"]
    assert output["endpointId"] == "estimate:g-after-f"
    assert output["context"]["objectId"] == "operator:g-after-f"
    assert output["context"]["scaleId"] == "scale:N"
    assert output["features"]["regularity"]["offset"] == 8
    assert output["features"]["constantDependencies"]["allowedBinderIds"] == ["u"]


def test_loss_weakening_without_nesting_evidence_stays_residual():
    source = _contract("a", offset=3)
    step = _step("weaken", ["statement:a"], "statement:goal")
    graph = _derivation([step])
    result = _run(
        graph, [source], goal="statement:goal",
        bindings=[_binding(step, rule_id="weaken-loss", parameters={"targetOffset": 5})],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[_scope(source, statement="statement:a")],
    )
    assert _goal_frontier(result, "statement:goal") == []
    assert any(row.get("stepRef") == step["stepRef"] for row in result["residuals"])


def test_loss_weakening_uses_declared_input_scale_nesting():
    source = _contract("a", offset=3)
    step = _step("weaken-valid", ["statement:a"], "statement:goal")
    graph = _derivation([step], [ref("check-run", "check:input-nesting")])
    result = _run(
        graph, [source], goal="statement:goal",
        bindings=[_binding(step, rule_id="weaken-loss", parameters={
            "targetOffset": 5,
            "nestednessRefs": [ref("check-run", "check:input-nesting")],
        })],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[_scope(source, statement="statement:a")],
    )
    output = _goal_frontier(result, "statement:goal")[0]["contractRecord"]
    assert output["features"]["regularity"]["offset"] == 5
    assert output["features"]["constantDependencies"]["allowedBinderIds"] == ["u"]


def test_generic_requirement_max_rule_stays_residual_without_req_descriptor():
    left = _contract("left", endpoint="estimate:goal", object_id="operator:goal")
    right = _contract("right", offset=5, dependencies=(), endpoint="estimate:goal",
                      object_id="operator:goal")
    step = _step("requirement-max", ["statement:left", "statement:right"], "statement:goal")
    graph = _derivation([step])
    result = _run(
        graph, [left, right], goal="statement:goal",
        bindings=[_binding(step, rule_id="combine-requirements", arity=2)],
        interfaces=[_interface("left", endpoint="estimate:goal", operator="operator:goal",
                                object_id="operator:goal", contract=left),
                    _interface("right", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=right),
                    _interface("out", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal")],
        scopes=[_scope(left, statement="statement:left"),
                _scope(right, statement="statement:right")],
    )
    assert _goal_frontier(result, "statement:goal") == []
    assert any(row.get("stepRef") == step["stepRef"] for row in result["residuals"])


def test_estimate_conjunction_is_not_admitted_without_its_exact_rule_evidence():
    left = _contract("left", offset=3, dependencies=("u",), endpoint="estimate:goal",
                     object_id="operator:goal")
    right = _contract("right", offset=5, dependencies=(), endpoint="estimate:goal",
                      object_id="operator:goal")
    step = _step("conjoin-estimates", ["statement:left", "statement:right"],
                 "statement:goal")
    graph = _derivation([step])
    result = _run(
        graph, [left, right], goal="statement:goal",
        bindings=[_binding(step, rule_id="combine-estimates", arity=2,
                           parameters={"leftEmbeddingRefs": [], "rightEmbeddingRefs": [],
                                       "nestednessRefs": []})],
        interfaces=[_interface("left", endpoint="estimate:goal", operator="operator:goal",
                                object_id="operator:goal", contract=left),
                    _interface("right", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=right),
                    _interface("out", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal")],
        scopes=[_scope(left, statement="statement:left"),
                _scope(right, statement="statement:right")],
    )
    assert _goal_frontier(result, "statement:goal") == []
    assert any(row.get("stepRef") == step["stepRef"] for row in result["residuals"])


def test_estimate_conjunction_uses_max_loss_and_permission_union_with_all_evidence():
    left = _contract("left", offset=3, dependencies=("u",), endpoint="estimate:goal",
                     object_id="operator:goal")
    right = _contract("right", offset=5, dependencies=(), endpoint="estimate:goal",
                      object_id="operator:goal")
    step = _step("conjoin-estimates-valid", ["statement:left", "statement:right"],
                 "statement:goal")
    required_evidence = [ref("check-run", item) for item in
                         ("check:embed-left", "check:embed-right", "check:nestedness")]
    graph = _derivation([step], required_evidence)
    result = _run(
        graph, [left, right], goal="statement:goal",
        bindings=[_binding(step, rule_id="combine-estimates", arity=2, parameters={
            "leftEmbeddingRefs": [ref("check-run", "check:embed-left")],
            "rightEmbeddingRefs": [ref("check-run", "check:embed-right")],
            "nestednessRefs": [ref("check-run", "check:nestedness")],
        })],
        interfaces=[_interface("left", endpoint="estimate:goal", operator="operator:goal",
                                object_id="operator:goal", contract=left),
                    _interface("right", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=right),
                    _interface("out", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal")],
        scopes=[_scope(left, statement="statement:left"),
                _scope(right, statement="statement:right")],
    )
    output = _goal_frontier(result, "statement:goal")[0]["contractRecord"]
    assert output["features"]["regularity"]["offset"] == 5
    assert output["features"]["constantDependencies"]["allowedBinderIds"] == ["u"]


def test_cycle_is_explicitly_unsupported_not_a_fixed_point_route():
    result = _run(
        _cyclic_derivation(), [], goal="A", bindings=[], interfaces=[], scopes=[]
    )
    assert result["status"] == "unsupported-cycle"
    assert result["complete"] is False
    assert result["residuals"]


def test_eight_statement_three_alternative_dag_matches_independent_oracle():
    # Each application is an identity transfer, so the oracle independently
    # enumerates all source routes and then reduces complete (loss, permission)
    # tuples. This checks graph propagation without using the evaluator's walk.
    source_scores = [(3, {"u"}), (5, set()), (4, {"u"})]
    sources = _independent_oracle_sources(source_scores)
    steps, incoming, graph = _independent_oracle_graph()

    # Exhaustive route-source enumeration over the tiny acyclic graph.
    candidates = [source_scores[index] for index in _enumerate_oracle_routes(incoming)]
    expected = _minimal_oracle_frontier(candidates)

    identity_output = _interface(
        "identity-output", endpoint="estimate:fixed", operator="operator:fixed",
        object_id="operator:fixed",
    )
    result = _run(
        graph, sources, goal="s7",
        bindings=_oracle_bindings(steps),
        interfaces=_oracle_interfaces(sources, identity_output),
        scopes=_oracle_scopes(sources),
    )
    replay = _run(
        graph, sources, goal="s7",
        bindings=_oracle_bindings(steps),
        interfaces=_oracle_interfaces(sources, identity_output),
        scopes=_oracle_scopes(sources),
    )
    actual = {
        (row["contractRecord"]["features"]["regularity"]["offset"],
         tuple(row["contractRecord"]["features"]["constantDependencies"]["allowedBinderIds"]))
        for row in _goal_frontier(result, "s7")
    }
    assert len(steps) <= 3 * (8 - 3)
    assert actual == expected == {(3, ("u",)), (5, ())}
    assert replay == result


def test_frontier_cap_reports_pending_work_without_negative_result():
    route_a = _contract("cap-a", offset=3, dependencies=("u",), endpoint="estimate:goal",
                        object_id="operator:goal")
    route_b = _contract("cap-b", offset=5, dependencies=(), endpoint="estimate:goal",
                        object_id="operator:goal")
    step_a = _step("cap-a", ["statement:cap-a"], "statement:goal")
    step_b = _step("cap-b", ["statement:cap-b"], "statement:goal")
    graph = _derivation([step_a, step_b])
    output = _interface("out", endpoint="estimate:goal", operator="operator:goal",
                        object_id="operator:goal")
    result = _run(
        graph, [route_a, route_b], goal="statement:goal",
        bindings=[_binding(step_a), _binding(step_b)],
        interfaces=[output,
                    _interface("a", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=route_a),
                    _interface("b", endpoint="estimate:goal", operator="operator:goal",
                               object_id="operator:goal", contract=route_b)],
        scopes=[_scope(route_a, statement="statement:cap-a"),
                _scope(route_b, statement="statement:cap-b")],
        bounds={"maxFrontierContractsPerStatement": 1},
    )
    assert result["status"] == "partial"
    assert result["complete"] is False
    assert result["coverage"]["pending"]
    assert _goal_frontier(result, "statement:goal")


def test_unknown_or_alternative_does_not_cache_a_negative_over_supported_route():
    source = _contract("a", endpoint="estimate:goal", object_id="operator:goal")
    unsupported = _step("unsupported", ["statement:a"], "statement:goal")
    supported = _step("supported", ["statement:a"], "statement:goal")
    graph = _derivation([unsupported, supported])
    output = _interface("out", endpoint="estimate:goal", operator="operator:goal",
                        object_id="operator:goal")
    result = _run(
        graph, [source], goal="statement:goal",
        bindings=[_binding(supported, output_interface="out")],
        interfaces=[output, _interface("input", endpoint="estimate:goal",
                                        operator="operator:goal", object_id="operator:goal",
                                        contract=source)],
        scopes=[_scope(source, statement="statement:a")],
    )
    assert _goal_frontier(result, "statement:goal")
    assert any(row.get("stepRef") == unsupported["stepRef"] for row in result["residuals"])
