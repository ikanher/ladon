"""Small native graph controls shared by the task 2.1 red proposal."""
from copy import deepcopy

from test_proof_contract_propagation import (
    _binding,
    _contract,
    _derivation,
    _interface,
    _run,
    _scope,
    _step,
)

from support.proofir_v3_native import ref


def route_a_route_b():
    route_a = _contract("route-a-source", offset=5, dependencies=("u",))
    route_b = _contract("route-b-source", offset=2, dependencies=())
    a1 = _step("route-a-1", ["route-a-source"], "route-a-mid1")
    a2 = _step("route-a-2", ["route-a-mid1"], "route-a-mid2")
    a3 = _step("route-a-3", ["route-a-mid2"], "goal")
    b1 = _step("route-b-direct", ["route-b-source"], "goal")
    steps = [a1, a2, a3, b1]
    graph = _derivation(steps)
    out = _interface("out")
    in_a = _interface("in-a", contract=route_a)
    in_b = _interface("in-b", contract=route_b)
    artifacts = [route_a, route_b]
    interfaces = [out, in_a, in_b]
    scopes = [_scope(route_a, statement="route-a-source"),
              _scope(route_b, statement="route-b-source")]
    bindings = [_binding(step, output_interface="out") for step in steps]
    desired = _contract("desired", offset=3, dependencies=())["payload"]["record"]
    return {
        "graph": graph, "artifacts": artifacts, "interfaces": interfaces,
        "scopes": scopes, "bindings": bindings, "steps": steps,
        "routeASteps": [a1["stepRef"], a2["stepRef"], a3["stepRef"]],
        "routeBSteps": [b1["stepRef"]], "desired": desired,
        "goalRef": ref("statement", "goal"),
    }


def run_forward(case, *, bounds=None):
    return _run(
        case["graph"], case["artifacts"], goal="goal", bindings=case["bindings"],
        interfaces=case["interfaces"], scopes=case["scopes"], bounds=bounds,
    )


def _default_route_priorities(case):
    return case.get("routePriorities", [
        {"rootStepRef": row["stepRef"], "sourceLocation": None,
         "sourceId": "fallback:" + row["stepRef"]["localId"],
         "line": None, "column": None, "heuristicPriority": 0}
        for row in case["bindings"]
    ])


def _choose(value, fallback):
    return fallback if value is None else value


def request_kwargs(case, *, reading_id="reading:paper-v1", bounds=None,
                   desired=None, bindings=None, interfaces=None, scopes=None,
                   artifacts=None, backward_choices=None, described_route_step_refs=None,
                   route_priorities=None):
    return {
        "derivation_artifact": case["graph"],
        "contract_artifacts": _choose(artifacts, case["artifacts"]),
        "goal_ref": case["goalRef"],
        "rule_bindings": _choose(bindings, case["bindings"]),
        "endpoint_interfaces": _choose(interfaces, case["interfaces"]),
        "scope_bindings": _choose(scopes, case["scopes"]),
        "desired_contract": deepcopy(_choose(desired, case["desired"])),
        "desired_reading_identity": {
            "readingId": reading_id,
            "interpretationDigest": "sha256:" + ("1" if reading_id.endswith("v1") else "2") * 64,
        },
        "described_route_step_refs": _choose(described_route_step_refs, case["routeASteps"]),
        "per_application_backward_choices": _choose(backward_choices, [
            {"stepRef": row["stepRef"], "choices": {}} for row in case["bindings"]
        ]),
        "route_priorities": _choose(route_priorities, _default_route_priorities(case)),
        "bounds": _choose(bounds, {}),
    }


def unsupported_and_missing_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )
    source = _contract("unsupported-source", offset=2, dependencies=())
    unsupported = _step("unsupported-implication", ["unsupported-source"], "goal")
    missing = _step("missing-provider", ["missing-source"], "goal")
    graph = _derivation([unsupported, missing])
    return {
        "graph": graph, "artifacts": [source],
        "interfaces": [_interface("out"), _interface("input", contract=source)],
        "scopes": [_scope(source, statement="unsupported-source")],
        "bindings": [_binding(unsupported, rule_id="arbitrary-implication")],
        "steps": [unsupported, missing], "routeASteps": [unsupported["stepRef"]],
        "routeBSteps": [missing["stepRef"]],
        "desired": _contract("unsupported-desired", offset=2, dependencies=())["payload"]["record"],
        "goalRef": ref("statement", "goal"),
    }


def unknown_feature_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )

    from support.proofir_v3_native import ENVIRONMENT, envelope
    source = _contract("unknown-source", offset=2, dependencies=())
    payload = deepcopy(source["payload"])
    payload["record"]["features"]["constantDependencies"] = {
        "state": "unknown", "allowedBinderIds": None, "reason": "fixture-unknown",
    }
    payload["provenance"]["completeness"] = "partial"
    source = envelope(
        "proofir.contract", payload, source["subjectRefs"],
        environment=ENVIRONMENT,
    )
    step = _step("unknown-identity", ["unknown-source"], "goal")
    graph = _derivation([step])
    return {
        "graph": graph, "artifacts": [source],
        "interfaces": [_interface("out"), _interface("input", contract=source)],
        "scopes": [_scope(source, statement="unknown-source")],
        "bindings": [_binding(step)], "steps": [step],
        "routeASteps": [step["stepRef"]], "routeBSteps": [],
        "desired": _contract("known-desired", offset=2, dependencies=())["payload"]["record"],
        "goalRef": ref("statement", "goal"),
    }


def multi_frontier_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )
    a = _contract("multi-a", offset=3, dependencies=("u",))
    b = _contract("multi-b", offset=5, dependencies=())
    step = _step("multi-identity", ["multi-source"], "goal")
    graph = _derivation([step])
    out = _interface("out")
    in_a = _interface("in-a", contract=a)
    in_b = _interface("in-b", contract=b)
    return {
        "graph": graph, "artifacts": [a, b], "interfaces": [out, in_a, in_b],
        "scopes": [_scope(a, statement="multi-source"), _scope(b, statement="multi-source")],
        "bindings": [_binding(step, output_interface="out")], "steps": [step],
        "routeASteps": [step["stepRef"]], "routeBSteps": [],
        "desired": _contract("multi-desired", offset=4, dependencies=())["payload"]["record"],
        "goalRef": ref("statement", "goal"),
    }


def substitution_mismatch_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )
    source = _contract("substitution-source", offset=2, dependencies=())
    first = _step("substitution-first", ["substitution-source"], "substitution-mid",
                  substitutions=[{"variable": "u", "termRef": ref("term", "term:u")}])
    second = _step("substitution-second", ["substitution-mid"], "goal",
                   substitutions=[{"variable": "u", "termRef": ref("term", "term:v")}])
    graph = _derivation([first, second])
    return {
        "graph": graph, "artifacts": [source],
        "interfaces": [_interface("out"), _interface("input", contract=source)],
        "scopes": [_scope(source, statement="substitution-source")],
        "bindings": [_binding(first), _binding(second)], "steps": [first, second],
        "routeASteps": [first["stepRef"], second["stepRef"]], "routeBSteps": [],
        "desired": source["payload"]["record"], "goalRef": ref("statement", "goal"),
    }


def provider_scope_mismatch_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )
    provider = _contract("other-scope-provider", offset=2, dependencies=(),
                         object_id="operator:other")
    step = _step("scope-mismatch", ["other-scope-provider"], "goal")
    graph = _derivation([step])
    return {
        "graph": graph, "artifacts": [provider],
        "interfaces": [_interface("out"), _interface("input", operator="operator:other",
                                                     object_id="operator:other", contract=provider)],
        "scopes": [_scope(provider, statement="other-scope-provider")],
        "bindings": [_binding(step)], "steps": [step],
        "routeASteps": [step["stepRef"]], "routeBSteps": [],
        "desired": _contract("desired-original", offset=2, dependencies=())["payload"]["record"],
        "goalRef": ref("statement", "goal"),
    }


def repeated_and_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )

    from support.proofir_v3_native import ref

    source = _contract("repeat-source", offset=3, dependencies=())
    step = _step("and-repeat", ["repeat-source", "repeat-source"], "goal")
    extra = [ref("check-run", value) for value in
             ("check:embed-left", "check:embed-right", "check:nested")]
    graph = _derivation([step], extra)
    output = _interface("out")
    input_interface = _interface("input", contract=source)
    binding = _binding(
        step, rule_id="combine-estimates", output_interface="out", arity=2,
        parameters={
            "leftEmbeddingRefs": [ref("check-run", "check:embed-left")],
            "rightEmbeddingRefs": [ref("check-run", "check:embed-right")],
            "nestednessRefs": [ref("check-run", "check:nested")],
        },
    )
    return {
        "graph": graph, "artifacts": [source], "interfaces": [output, input_interface],
        "scopes": [_scope(source, statement="repeat-source")], "bindings": [binding],
        "steps": [step], "routeASteps": [step["stepRef"]],
        "routeBSteps": [], "desired": source["payload"]["record"],
        "goalRef": ref("statement", "goal"),
    }


def split_context_and_case():
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )

    from support.proofir_v3_native import ref

    left = _contract("left-branch", offset=2, dependencies=())
    right = _contract("right-branch", offset=3, dependencies=())
    step = _step("and-split-context", ["left-branch", "right-branch"], "goal", context="context:join")
    extra = [ref("local-context", "context:left"), ref("local-context", "context:right")]
    graph = _derivation([step], extra)
    interfaces = [
        _interface("out"),
        _interface("in-left", contract=left),
        _interface("in-right", contract=right),
    ]
    return {
        "graph": graph, "artifacts": [left, right], "interfaces": interfaces,
        "scopes": [_scope(left, statement="left-branch", context="context:left"),
                   _scope(right, statement="right-branch", context="context:right")],
        "bindings": [_binding(step, rule_id="combine-estimates", output_interface="out", arity=2,
                              parameters={"leftEmbeddingRefs": [ref("check-run", "check:source")],
                                          "rightEmbeddingRefs": [ref("check-run", "check:interface")],
                                          "nestednessRefs": [ref("check-run", "check:source")]})],
        "steps": [step], "routeASteps": [step["stepRef"]], "routeBSteps": [],
        "desired": _contract("desired-split", offset=3, dependencies=())["payload"]["record"],
        "goalRef": ref("statement", "goal"),
    }




def composition_case(*, wrong_middle=False):
    from test_proof_contract_propagation import (
        _binding,
        _contract,
        _derivation,
        _interface,
        _scope,
        _step,
    )
    left = _contract("compose-left", offset=1, dependencies=(), object_id="operator:composite")
    right = _contract("compose-right", offset=2, dependencies=(), object_id="operator:composite")
    step = _step("compose-app", ["compose-left", "compose-right"], "goal")
    middle_type = "type:wrong" if wrong_middle else "type:B"
    left_iface = _interface(
        "compose-left-iface", contract=left, endpoint="estimate:f", operator="operator:composite",
        object_id="operator:composite", input_type="type:A", output_type="type:B",
        input_scale="scale:N", output_scale="scale:N", input_norm="norm:N", output_norm="norm:N",
    )
    right_iface = _interface(
        "compose-right-iface", contract=right, endpoint="estimate:f", operator="operator:composite",
        object_id="operator:composite", input_type=middle_type, output_type="type:C",
        input_scale="scale:N", output_scale="scale:N", input_norm="norm:N", output_norm="norm:N",
    )
    out_iface = _interface(
        "compose-output", endpoint="estimate:f", operator="operator:composite",
        object_id="operator:composite", input_type="type:A", output_type="type:C",
        input_scale="scale:N", output_scale="scale:N", input_norm="norm:N", output_norm="norm:N",
    )
    binding = _binding(
        step, rule_id="compose", arity=2, output_interface="compose-output",
        parameters={"compositeOperatorId": "operator:composite"},
    )
    return {
        "graph": _derivation([step]), "artifacts": [left, right],
        "interfaces": [out_iface, left_iface, right_iface],
        "scopes": [_scope(left, statement="compose-left"), _scope(right, statement="compose-right")],
        "bindings": [binding], "steps": [step],
        "routeASteps": [step["stepRef"]], "routeBSteps": [],
        "desired": _contract("compose-desired", offset=3, dependencies=(),
                              object_id="operator:composite")["payload"]["record"],
        "goalRef": ref("statement", "goal"),
        "routePriorities": [{"rootStepRef": step["stepRef"], "sourceLocation": None,
                              "sourceId": "fallback:compose-app", "line": None,
                              "column": None, "heuristicPriority": 0}],
    }
