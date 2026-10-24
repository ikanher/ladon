"""Adversarial checks added after the independent contract falsification."""

import copy
import hashlib

import pytest

from ladon.proof_contract_refinement import (
    _refinement_digest,
    check_rational_refinement,
    create_refinement_branch,
)


def _finding():
    return {
        "id": "finding-adversarial",
        "status": "abstract-countermodel",
        "discrepancy": {"claim": "x >= 0"},
        "witness": {"id": "w", "assignment": {"x": "-1"}},
    }


def _predicate(right="0"):
    return {"op": "ge", "left": {"var": "x"}, "right": {"rat": right}}


def _branch(tmp_path, expression=None):
    source = "Assume x is nonnegative.\n"
    path = tmp_path / "paper.txt"
    path.write_text(source, encoding="utf-8")
    constraint = {
        "id": "c1",
        "expression": _predicate() if expression is None else expression,
        "justification": {
            "kind": "source-cited-refinement",
            "source": {
                "path": path.name,
                "startLine": 1,
                "endLine": 1,
                "quote": source.rstrip("\n"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            },
            "nonclaim": "Span validation does not certify formula fidelity.",
        },
    }
    return create_refinement_branch(_finding(), [constraint], source_root=tmp_path)


def _goal():
    return {
        "variables": ["x"],
        "premises": [],
        "conclusion": _predicate(),
    }


def test_result_verification_is_type_sensitive_for_boolean_fields(tmp_path):
    branch = _branch(tmp_path)
    result = check_rational_refinement(
        branch, _goal(), {"x": "-1"}, source_root=tmp_path
    )
    forged = copy.deepcopy(result)
    forged["originalClaimRefuted"] = 0

    # Recomputing and comparing canonical serialized bytes distinguishes 0
    # from false even though Python's ordinary equality treats them as equal.
    from ladon.proof_contract_refinement import verify_rational_refinement_result

    with pytest.raises(ValueError):
        verify_rational_refinement_result(
            forged, branch, _goal(), {"x": "-1"}, source_root=tmp_path
        )


def test_assignment_key_order_is_canonical_but_literal_spelling_is_bound(tmp_path):
    branch = _branch(tmp_path)
    base = {
        "variables": ["x", "y"],
        "premises": [],
        "conclusion": _predicate(),
    }
    first = check_rational_refinement(
        branch, base, {"x": "1/1", "y": "2"}, source_root=tmp_path
    )
    reordered = check_rational_refinement(
        branch, base, {"y": "2", "x": "1/1"}, source_root=tmp_path
    )
    equivalent_value = check_rational_refinement(
        branch, base, {"x": 1, "y": "2"}, source_root=tmp_path
    )

    assert first["checkId"] == reordered["checkId"]
    assert first["checkId"] != equivalent_value["checkId"]


def test_digest_valid_branch_does_not_claim_authentic_parent_lineage(tmp_path):
    branch = _branch(tmp_path)
    branch["parentId"] = "caller-supplied-parent-label"
    branch["id"] = _refinement_digest(branch)

    result = check_rational_refinement(
        branch, _goal(), {"x": "-1"}, source_root=tmp_path
    )

    assert result["witnessCheck"]["status"] == "outside-assumptions"
    assert result["originalClaimRefuted"] is False
    assert any("encoded rational goal" in item for item in result["nonclaims"])


def test_false_added_predicate_is_only_outside_assumptions(tmp_path):
    branch = _branch(tmp_path, _predicate("1"))

    result = check_rational_refinement(
        branch, _goal(), {"x": "0"}, source_root=tmp_path
    )

    assert result["witnessCheck"]["status"] == "outside-assumptions"
    assert result["originalClaimRefuted"] is False


def test_division_by_zero_in_added_predicate_is_rejected(tmp_path):
    expression = {
        "op": "eq",
        "left": {"op": "div", "args": [{"rat": "1"}, {"rat": "0"}]},
        "right": {"rat": "0"},
    }
    branch = _branch(tmp_path, expression)

    with pytest.raises(ValueError, match="division by zero"):
        check_rational_refinement(
            branch, _goal(), {"x": "0"}, source_root=tmp_path
        )
