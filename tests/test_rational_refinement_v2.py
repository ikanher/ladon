"""Candidate regressions for frozen branch-semantics contract #1115.

These tests intentionally live outside the active test tree. Root may review
and freeze them after implementation is available; this author does not run
them or modify production code.
"""

import copy
import hashlib

import pytest

from ladon.proof_contract_refinement import (
    check_rational_refinement,
    create_refinement_branch,
    verify_rational_refinement_result,
)


def _finding():
    return {
        "id": "finding-rational-1",
        "status": "abstract-countermodel",
        "discrepancy": {"claim": "x is nonnegative", "observed": "x = -1"},
        "witness": {"id": "witness-1", "assignment": {"x": "-1"}},
    }


def _predicate(op="ge", left=None, right=None):
    return {
        "op": op,
        "left": {"var": "x"} if left is None else left,
        "right": {"rat": "0"} if right is None else right,
    }


def _goal(*, conclusion=None, premises=None):
    return {
        "variables": ["x"],
        "premises": [] if premises is None else premises,
        "conclusion": _predicate() if conclusion is None else conclusion,
    }


def _source_branch(tmp_path, *, expression=None, text="Assume x is nonnegative.\n"):
    source_path = tmp_path / "paper.txt"
    source_path.write_text(text, encoding="utf-8")
    constraint = {
        "id": "domain-nonnegative",
        "expression": _predicate() if expression is None else expression,
        "justification": {
            "kind": "source-cited-refinement",
            "source": {
                "path": "paper.txt",
                "startLine": 1,
                "endLine": 1,
                "quote": text.rstrip("\n"),
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            },
            "nonclaim": "Span validation does not certify formula fidelity.",
        },
    }
    return create_refinement_branch(_finding(), [constraint], source_root=tmp_path)


def _repair_branch(tmp_path, *, expression=None):
    repair = {
        "id": "repair-nonnegative-domain",
        "expression": _predicate() if expression is None else expression,
        "justification": {
            "kind": "proposed-repair",
            "rationale": "Try restricting the domain to nonnegative inputs.",
        },
    }
    return create_refinement_branch(_finding(), [repair], source_root=tmp_path)


def test_exact_predicate_ast_becomes_a_checked_derived_premise(tmp_path):
    branch = _source_branch(tmp_path)
    base = _goal()
    assignment = {"x": "-1"}

    result = check_rational_refinement(branch, base, assignment, source_root=tmp_path)

    _assert_derived_identity(result, branch, base)
    assert result["assignment"] == assignment
    assert result["checkerIdentity"]
    assert result["witnessCheck"]["status"] == "outside-assumptions"
    assert result["checkId"]
    assert result["resultDigest"]
    assert result["originalClaimRefuted"] is False
    assert result["sourceFormulaFidelity"] == "unverified"


def _assert_derived_identity(result, branch, base):
    assert result["schema"] == "ladon-rational-refinement-check-v1"
    assert result["branchId"] == branch["id"]
    assert result["branchKind"] == "source-cited-refinement"
    assert result["originalFindingId"] == _finding()["id"]
    assert result["baseGoal"] == base
    assert result["derivedGoal"]["premises"] == [branch["constraints"][0]["expression"]]
    assert result["baseGoalSha256"]
    assert result["derivedGoalSha256"]


def test_source_citation_does_not_claim_formula_fidelity_or_refute_original(tmp_path):
    branch = _source_branch(
        tmp_path,
        expression=_predicate("ge", {"var": "x"}, {"rat": "100"}),
    )

    result = check_rational_refinement(
        branch, _goal(), {"x": "101"}, source_root=tmp_path
    )

    assert result["branchKind"] == "source-cited-refinement"
    assert result["witnessCheck"]["status"] == "not-counterexample"
    assert result["sourceFormulaFidelity"] == "unverified"
    assert result["originalClaimRefuted"] is False


def test_proposed_repair_check_remains_separate_from_original_claim(tmp_path):
    branch = _repair_branch(tmp_path)

    result = check_rational_refinement(
        branch, _goal(), {"x": "1"}, source_root=tmp_path
    )

    assert result["branchKind"] == "proposed-repair"
    assert result["witnessCheck"]["status"] == "not-counterexample"
    assert result["originalClaimRefuted"] is False
    assert "not evidence for the original claim" in " ".join(result["nonclaims"])


def test_child_branch_checks_all_cumulative_constraints(tmp_path):
    parent = _source_branch(tmp_path)
    second_source = "Assume x is at most ten.\n"
    source_path = tmp_path / "upper.txt"
    source_path.write_text(second_source, encoding="utf-8")
    addition = {
        "id": "domain-upper-bound",
        "expression": _predicate("le", {"var": "x"}, {"rat": "10"}),
        "justification": {
            "kind": "source-cited-refinement",
            "source": {
                "path": "upper.txt",
                "startLine": 1,
                "endLine": 1,
                "quote": second_source.rstrip("\n"),
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            },
            "nonclaim": "Span validation does not certify formula fidelity.",
        },
    }
    child = create_refinement_branch(parent, [addition], source_root=tmp_path)

    result = check_rational_refinement(
        child, _goal(), {"x": "11"}, source_root=tmp_path
    )

    assert [row["constraintId"] for row in result["constraintChecks"]] == [
        "domain-nonnegative",
        "domain-upper-bound",
    ]
    assert len(result["derivedGoal"]["premises"]) == 2
    assert result["witnessCheck"]["status"] == "outside-assumptions"


@pytest.mark.parametrize(
    "expression",
    [
        "x >= 0",
        {"predicate": {"op": "ge", "left": {"var": "x"}, "right": {"rat": "0"}}},
        {"op": "add", "args": [{"var": "x"}, {"rat": "0"}]},
        {"op": "ge", "left": {"var": "y"}, "right": {"rat": "0"}},
        {"op": "ge", "left": {"var": "x"}, "right": {"rat": True}},
    ],
)
def test_unsupported_or_invalid_expression_is_rejected(tmp_path, expression):
    branch = _source_branch(tmp_path, expression=expression)

    with pytest.raises((TypeError, ValueError)):
        check_rational_refinement(
            branch, _goal(), {"x": "1"}, source_root=tmp_path
        )


def test_derived_goal_respects_existing_rational_premise_bound(tmp_path):
    branch = _source_branch(tmp_path)
    base = _goal(premises=[_predicate("ge", {"var": "x"}, {"rat": "-100"})] * 64)

    with pytest.raises((TypeError, ValueError)):
        check_rational_refinement(
            branch, base, {"x": "1"}, source_root=tmp_path
        )


@pytest.mark.parametrize("changed", ["branch", "base-goal", "assignment"])
def test_result_verifier_rejects_replay_under_changed_semantic_identity(
    tmp_path, changed
):
    branch = _source_branch(tmp_path)
    base = _goal()
    assignment = {"x": "-1"}
    result = check_rational_refinement(branch, base, assignment, source_root=tmp_path)
    current_branch, current_base, current_assignment = branch, base, assignment

    if changed == "branch":
        current_branch = _source_branch(
            tmp_path,
            expression=_predicate("ge", {"var": "x"}, {"rat": "1"}),
        )
    elif changed == "base-goal":
        current_base = _goal(conclusion=_predicate("gt"))
    else:
        current_assignment = {"x": "1"}

    with pytest.raises((TypeError, ValueError)):
        verify_rational_refinement_result(
            result,
            current_branch,
            current_base,
            current_assignment,
            source_root=tmp_path,
        )


def test_result_verifier_rejects_tampered_derived_check(tmp_path):
    branch = _source_branch(tmp_path)
    base = _goal()
    assignment = {"x": "-1"}
    result = check_rational_refinement(branch, base, assignment, source_root=tmp_path)
    forged = copy.deepcopy(result)
    forged["witnessCheck"]["status"] = "counterexample"

    with pytest.raises((TypeError, ValueError)):
        verify_rational_refinement_result(
            forged, branch, base, assignment, source_root=tmp_path
        )


def test_stale_source_span_invalidates_branch_check(tmp_path):
    branch = _source_branch(tmp_path)
    (tmp_path / "paper.txt").write_text("Assume x is negative.\n", encoding="utf-8")

    with pytest.raises((TypeError, ValueError, OSError)):
        check_rational_refinement(
            branch, _goal(), {"x": "1"}, source_root=tmp_path
        )

