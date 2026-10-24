"""Independent finite AND/OR enumeration without the production comparator."""

import random
from itertools import product

import pytest
from support.proofir_v3_native import ref
from test_proof_contract_propagation import (
    _binding,
    _contract,
    _derivation,
    _interface,
    _run,
    _scope,
    _step,
)


def fixture(seed):
    rng = random.Random(seed)
    scores = [(rng.randrange(6), bool(rng.randrange(2))) for _ in range(3)]
    present = [i for i in range(3) if seed % 4 != i]
    sources = [_contract(f"seed{i}", offset=scores[i][0],
                         dependencies=("u",) if scores[i][1] else ()) for i in present]
    graph_rows = []
    for node in range(3, 8):
        for alternative in range(3):
            parents = [rng.randrange(node) for _ in range(1 + rng.randrange(2))]
            graph_rows.append((node, parents, f"n{node}a{alternative}"))
    return scores, present, sources, graph_rows


def exhaustive(scores, present, graph_rows):
    # Keep every distinct complete feature tuple, including dominated ones.
    # This recurrence does not call or reproduce production antichain reduction.
    values = {i: {scores[i]} if i in present else set() for i in range(3)}
    for node, parents, _ in graph_rows:
        candidates = product(*(values[parent] for parent in parents))
        values.setdefault(node, set()).update(
            (max(pair[0] for pair in combo), any(pair[1] for pair in combo))
            for combo in candidates
        )
    return values


def nondominated(values):
    return {value for value in values if not any(
        other != value and other[0] <= value[0] and other[1] <= value[1]
        for other in values
    )}


def native_request(sources, graph_rows):
    steps = [_step(name, [f"n{parent}" for parent in parents], f"n{node}")
             for node, parents, name in graph_rows]
    evidence = ref("check-run", "check:nesting")
    parameters = {key: [evidence] for key in (
        "leftEmbeddingRefs", "rightEmbeddingRefs", "nestednessRefs")}
    bindings = [_binding(step, rule_id="combine-estimates", arity=2, parameters=parameters)
                if len(step["premiseRefs"]) == 2 else _binding(step) for step in steps]
    interfaces = [_interface("out"), *[_interface(f"in{i}", contract=source)
                                       for i, source in enumerate(sources)]]
    scopes = [_scope(source, statement="n" + source["payload"]["contractId"][4:])
              for source in sources]
    return _derivation(steps, [evidence]), bindings, interfaces, scopes


def feature_pairs(result, statement):
    frontier = next(row["contracts"] for row in result["frontiers"]
                    if row["statementRef"] == ref("statement", statement))
    return {(row["contractRecord"]["features"]["regularity"]["offset"],
             bool(row["contractRecord"]["features"]["constantDependencies"]["allowedBinderIds"]))
            for row in frontier}


@pytest.mark.parametrize("seed", range(64))
def test_eight_node_and_or_dag_matches_exhaustive_complete_tuple_oracle(seed):
    scores, present, sources, graph_rows = fixture(seed)
    expected = exhaustive(scores, present, graph_rows)
    graph, bindings, interfaces, scopes = native_request(sources, graph_rows)
    result = _run(graph, sources, goal="n7", bindings=bindings,
                  interfaces=interfaces, scopes=scopes)
    assert feature_pairs(result, "n7") == nondominated(expected[7]), (seed, result)
    assert not any(row["code"].endswith("-cap") for row in result["residuals"])
