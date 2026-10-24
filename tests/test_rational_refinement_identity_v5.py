"""Pin semantic digest preimages and combined rational-AST bounds."""

import hashlib
import json

import pytest

from ladon.proof_contract_refinement import (
    _refinement_digest,
    check_rational_refinement,
    create_refinement_branch,
)


def _canonical_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _branch(tmp_path):
    path = tmp_path / "paper.txt"
    quote = "Assume x is nonnegative."
    path.write_text(quote + "\n", encoding="utf-8")
    finding = {
        "id": "finding-é",
        "status": "abstract-countermodel",
        "discrepancy": {"claim": "x >= 0"},
        "witness": {"id": "w", "assignment": {"x": "-1"}},
    }
    predicate = {
        "op": "ge",
        "left": {"var": "x"},
        "right": {"rat": "0"},
    }
    constraint = {
        "id": "c1",
        "expression": predicate,
        "justification": {
            "kind": "source-cited-refinement",
            "source": {
                "path": path.name,
                "startLine": 1,
                "endLine": 1,
                "quote": quote,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            },
            "nonclaim": "Span validation does not certify formula fidelity.",
        },
    }
    return create_refinement_branch(finding, [constraint], source_root=tmp_path)


def _balanced_expression(leaves):
    if leaves == 1:
        return {"var": "x"}
    left_leaves = leaves // 2
    return {
        "op": "add",
        "args": [
            _balanced_expression(left_leaves),
            _balanced_expression(leaves - left_leaves),
        ],
    }


def test_digests_match_documented_canonical_preimages(tmp_path):
    branch = _branch(tmp_path)
    branch["originalFinding"]["id"] = "finding-é"
    branch["id"] = _refinement_digest(branch)
    base = {
        "variables": ["x"],
        "premises": [],
        "conclusion": {
            "op": "ge",
            "left": {"var": "x"},
            "right": {"rat": "0"},
        },
    }
    result = check_rational_refinement(
        branch, base, {"x": "-1"}, source_root=tmp_path
    )

    request_keys = {
        "schema",
        "branchId",
        "branchKind",
        "originalFindingId",
        "baseGoalSha256",
        "derivedGoalSha256",
        "assignment",
        "checkerIdentity",
    }
    request = {key: result[key] for key in request_keys}
    expected_check_id = hashlib.sha256(_canonical_bytes(request)).hexdigest()
    result_preimage = {key: value for key, value in result.items() if key != "resultDigest"}
    expected_result_digest = hashlib.sha256(_canonical_bytes(result_preimage)).hexdigest()

    assert result["checkId"] == "sha256:" + expected_check_id
    assert result["resultDigest"] == "sha256:" + expected_result_digest


def test_aggregate_ast_node_bound_applies_after_adding_branch_predicate(tmp_path):
    branch = _branch(tmp_path)
    premises = [
        {"op": "ge", "left": _balanced_expression(1023), "right": {"rat": "0"}},
        {"op": "ge", "left": _balanced_expression(1022), "right": {"rat": "0"}},
    ]
    base = {
        "variables": ["x"],
        "premises": premises,
        "conclusion": {"op": "ge", "left": {"var": "x"}, "right": {"rat": "0"}},
    }

    # Base goal consumes 4095 AST nodes; one added predicate takes the derived
    # goal over the existing rational checker limit of 4096.
    with pytest.raises(ValueError, match="goal exceeds 4096 AST nodes"):
        check_rational_refinement(
            branch, base, {"x": "0"}, source_root=tmp_path
        )
