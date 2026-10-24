"""Atomic capture validation keeps the admitted builtin Nat semantics."""

import importlib
import json
from pathlib import Path

import pytest


def _capture():
    path = Path(__file__).parent / "fixtures/proof_contract_source_obligations/closed-goal.json"
    return json.loads(path.read_text())


def _expected():
    return {"kind": "forallNat2", "leftOperator": "ObligationsRed.N2",
            "map": "ObligationsRed.F2", "constantName": "ObligationsRed.C",
            "inputScale": "ObligationsRed.N1", "offset": 1}


@pytest.mark.parametrize("name", ["instLENat", "instMulNat", "instAddNat", "instOfNatNat"])
def test_coarse_symbol_match_does_not_authorize_custom_instances(name):
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    capture = _capture()
    payload = json.loads(capture["goal"]["typeStructural"].split(":", 1)[1])
    node = next(row for row in payload["nodes"] if row[:2] == ["const", "`" + name])
    node[1] = "`Custom." + name
    capture["goal"]["typeStructural"] = "ladon-expr-dag-v1:" + json.dumps(payload)
    with pytest.raises((ValueError, TypeError)):
        api._validate_captured_requirement(capture, _expected())


def test_structural_sharing_cannot_create_an_unbounded_expansion():
    codec = importlib.import_module("ladon._proof_contract_source_obligations_codec")
    nodes = [["const", "`Nat", "[]"]]
    for _ in range(30):
        last = len(nodes) - 1
        nodes.append(["app", last, last])
    text = "ladon-expr-dag-v1:" + json.dumps({"nodes": nodes, "root": len(nodes) - 1})
    with pytest.raises((ValueError, TypeError)):
        codec._decode_dag(text)


def test_cached_subtree_height_counts_toward_depth_limit():
    codec = importlib.import_module("ladon._proof_contract_source_obligations_codec")
    nodes = [["const", "`Nat", "[]"]]
    for _ in range(40):
        nodes.append(["app", len(nodes) - 1, 0])
    tall = len(nodes) - 1
    previous = tall
    for _ in range(40):
        nodes.append(["app", 0, previous])
        previous = len(nodes) - 1
    nodes.append(["app", tall, previous])
    text = "ladon-expr-dag-v1:" + json.dumps({"nodes": nodes, "root": len(nodes) - 1})
    with pytest.raises((ValueError, TypeError)):
        codec._decode_dag(text)
