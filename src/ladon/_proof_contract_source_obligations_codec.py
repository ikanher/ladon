"""Bounded decoder and exact checker for captured closed forall goals."""
from __future__ import annotations

import json
import re

from ladon._source_goal_protocol import validate_structural_text

from ._proof_contract_source_obligations_formula import _formula_symbols

MAX_DAG_BYTES = 1024**2
MAX_DAG_NODES = 4096
MAX_DAG_DEPTH = 64
MAX_EXPANDED_NODES = 65536

def _validate_captured_requirement(capture, expected):
    goal = _selected_goal(capture)
    _validate_goal_locals(goal.get("localContext", []))
    actual = _formula_symbols(_decode_dag(_structural_text(goal)))
    _compare_symbols(actual, expected)


def _selected_goal(capture):
    if not isinstance(capture, dict) or not isinstance(capture.get("goal"), dict):
        raise TypeError("capture has no selected goal")
    return capture["goal"]


def _validate_goal_locals(locals_):
    if not isinstance(locals_, list) or len(locals_) > 1:
        raise ValueError("captured goal has visible proof locals")
    for row in locals_:
        if not isinstance(row, dict) or row.get("implementationDetail") is not True:
            raise ValueError("captured goal has visible proof locals")


def _structural_text(goal):
    structural = goal.get("typeStructural")
    if not isinstance(structural, str) or len(structural.encode()) > MAX_DAG_BYTES:
        raise ValueError("captured structural expression exceeds byte limit")
    validate_structural_text(structural)
    return structural


def _compare_symbols(actual, expected):
    if expected.get("kind") != "forallNat2":
        raise ValueError("unsupported captured requirement kind")
    keys = ("kind", "leftOperator", "map", "constantName", "inputScale", "offset")
    if any(actual.get(key) != expected.get(key) for key in keys):
        raise ValueError("captured closed target differs from selected requirement")


def _decode_dag(text):
    prefix = "ladon-expr-dag-v1:"
    if not text.startswith(prefix):
        raise ValueError("unknown structural expression codec")
    raw = text[len(prefix):]
    if len(raw.encode()) > MAX_DAG_BYTES:
        raise ValueError("structural DAG exceeds byte cap")
    value = json.loads(raw)
    nodes, root = value.get("nodes"), value.get("root")
    if not isinstance(nodes, list) or len(nodes) > MAX_DAG_NODES or type(root) is not int:
        raise ValueError("structural DAG node cap or root is invalid")
    memo, visiting, expanded, heights = {}, set(), {}, {}
    def visit(index, depth=0):
        if type(index) is not int or not 0 <= index < len(nodes) or depth > MAX_DAG_DEPTH:
            raise ValueError("malformed structural DAG reference or depth")
        if index in memo:
            if depth + heights[index] > MAX_DAG_DEPTH:
                raise ValueError("structural DAG exceeds depth bound")
            return memo[index]
        if index in visiting:
            raise ValueError("structural DAG contains a cycle")
        visiting.add(index)
        row = nodes[index]
        if not isinstance(row, list) or not row:
            raise ValueError("malformed structural node")
        tag = row[0]
        if tag == "const" and len(row) == 3:
            name = _decode_name(row[1]); levels = _decode_levels(row[2])
            result = {"const": name, "levels": levels}
            children = []
        elif tag == "bvar" and len(row) == 2 and type(row[1]) is int:
            result, children = {"bvar": row[1]}, []
        elif tag == "lit" and len(row) == 2 and isinstance(row[1], str):
            match = re.fullmatch(r"Lean\.Literal\.natVal (0|[1-9][0-9]{0,63})", row[1])
            if match is None:
                raise ValueError("unsupported natural literal encoding")
            number = int(match.group(1)); result, children = {"nat": number}, []
        elif tag == "app" and len(row) == 3:
            children = [visit(row[1], depth+1), visit(row[2], depth+1)]
            result = {"app": children}
        elif tag == "forallE" and len(row) == 5:
            name = _decode_name(row[1], local=True)
            if row[2] != "Lean.BinderInfo.default":
                raise ValueError("unsupported forall binder annotation")
            domain = visit(row[3], depth+1); body = visit(row[4], depth+1)
            result, children = {"forallE": {"name": name, "binderInfo": "explicit",
                "type": domain, "body": body}}, [domain, body]
        else:
            raise ValueError("unsupported structural DAG node")
        size = 1 + sum(expanded.get(id(child), 1) for child in children)
        if size > MAX_EXPANDED_NODES:
            raise ValueError("expanded structural expression exceeds size bound")
        expanded[id(result)] = size
        heights[index] = 1 + max((heights[child_index] for child_index in _child_indices(row)), default=0)
        memo[index] = result
        visiting.remove(index)
        return result
    decoded = visit(root)
    if len(memo) != len(nodes):
        raise ValueError("unreachable structural DAG nodes are not accepted")
    return decoded


def _decode_name(value, local=False):
    if not isinstance(value, str) or not value.startswith("`"):
        raise ValueError("unsupported structural name representation")
    name = value[1:]
    known = {"Nat", "LE.le", "HMul.hMul", "HAdd.hAdd", "OfNat.ofNat",
        "instLENat", "instHMul", "instMulNat", "instHAdd", "instAddNat", "instOfNatNat"}
    if (name not in known and re.fullmatch(r"[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+", name) is None
            and not (local and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))):
        raise ValueError("malformed or unsupported qualified structural name")
    return name


def _child_indices(row):
    if row[0] == "app":
        return (row[1], row[2])
    if row[0] == "forallE":
        return (row[3], row[4])
    return ()


def _decode_levels(value):
    if value == "[]":
        return []
    if value == "[Lean.Level.zero]":
        return ["0"]
    if value == "[Lean.Level.zero, Lean.Level.zero, Lean.Level.zero]":
        return ["0", "0", "0"]
    if value == "[Lean.Level.zero, Lean.Level.zero]":
        return ["0", "0"]
    raise ValueError("unsupported universe level encoding")


