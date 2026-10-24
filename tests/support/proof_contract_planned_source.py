"""Attributed three-step method over independently observed Lean source atoms."""

from test_proof_contract_propagation import _binding, _derivation, _interface, _scope, _step

from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest
from support.proofir_v3_native import envelope, ref


def build_plan_request(snapshots):
    artifacts = _source_artifacts(snapshots)
    environment = snapshots["endpoint"]["environment"]
    type_id = snapshots["endpoint"]["contract"]["telescope"][0]["typeId"]

    def iface(name, inp, out, fun, artifact=None):
        endpoint = f"estimate:ThreeSteps.{out}:ThreeSteps.{inp}:ThreeSteps.{fun}"
        return _interface(
            name,
            endpoint=endpoint,
            operator=f"operator:ThreeSteps.{fun}",
            object_id=f"operator:ThreeSteps.{fun}",
            domain="domain:" + type_id,
            representation="representation:original",
            input_type=type_id,
            output_type=type_id,
            input_scale=f"scale:ThreeSteps.{inp}",
            output_scale=f"scale:ThreeSteps.{out}",
            input_norm=f"norm:ThreeSteps.{inp}",
            output_norm=f"norm:ThreeSteps.{out}",
            conclusion=endpoint + ":conclusion",
            contract=artifact,
        )

    first = _step("inner-compose", ["first", "second"], "inner")
    second = _step("outer-compose", ["inner", "third"], "outer")
    alt = _step("alternative", ["alternate"], "goal")
    third = _step("finish", ["outer"], "goal")
    steps = [first, second, third, alt]
    graph0 = _derivation(steps)
    graph = envelope(
        "proofir.derivation", graph0["payload"], graph0["subjectRefs"], environment=environment
    )
    interfaces = [
        iface("first", "N0", "N1", "F1", artifacts["firstBound"]),
        iface("second", "N1", "N2", "F2", artifacts["secondBound"]),
        iface("third", "N2", "N3", "F3", artifacts["thirdBound"]),
        iface("inner", "N0", "N2", "G"),
        iface("goal", "N0", "N3", "H"),
        iface("alternate", "N0", "N3", "H", artifacts["alternateBound"]),
    ]
    scopes = _source_scopes(snapshots, artifacts)
    bindings = [
        _binding(
            first,
            rule_id="compose",
            output_interface="inner",
            arity=2,
            parameters={"compositeOperatorId": "operator:ThreeSteps.G"},
        ),
        _binding(
            second,
            rule_id="compose",
            output_interface="goal",
            arity=2,
            parameters={"compositeOperatorId": "operator:ThreeSteps.H"},
        ),
        _binding(third, output_interface="goal"),
        _binding(alt, output_interface="goal"),
    ]
    request = ContractObligationPlanRequest(
        derivation_artifact=graph,
        contract_artifacts=[
            artifacts[n] for n in ["firstBound", "secondBound", "thirdBound", "alternateBound"]
        ],
        goal_ref=ref("statement", "goal"),
        rule_bindings=bindings,
        endpoint_interfaces=interfaces,
        scope_bindings=scopes,
        desired_contract=snapshots["endpoint"]["contract"],
        desired_reading_identity={
            "readingId": "reading:three-steps-described",
            "interpretationDigest": "sha256:" + "3" * 64,
        },
        described_route_step_refs=[s["stepRef"] for s in [first, second, third]],
        per_application_backward_choices=[
            {"stepRef": s["stepRef"], "choices": {"lossSplits": [[0, 0]]} if i < 2 else {}}
            for i, s in enumerate(steps)
        ],
        route_priorities=[
            {
                "rootStepRef": s["stepRef"],
                "sourceLocation": None,
                "sourceId": "fallback:" + s["stepRef"]["localId"],
                "line": None,
                "column": None,
                "heuristicPriority": 0,
            }
            for s in steps
        ],
        bounds={},
    )
    return request


def _source_artifacts(snapshots):
    return {
        n: next(a for a in s["artifacts"] if a["artifactKind"] == "proofir.contract")
        for n, s in snapshots.items()
    }


def _source_scopes(snapshots, artifacts):
    scopes = []
    for n, statement in [
        ("firstBound", "first"),
        ("secondBound", "second"),
        ("thirdBound", "third"),
        ("alternateBound", "alternate"),
    ]:
        scope = _scope(artifacts[n], statement=statement)
        scope["binderMap"] = [
            {"fromBinderId": b["binderId"], "toBinderId": b["binderId"]}
            for b in snapshots[n]["contract"]["telescope"]
        ]
        scopes.append(scope)
    return scopes
