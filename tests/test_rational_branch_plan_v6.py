"""Frozen red acceptance tests for board contract #394, superseding #393."""

import copy
import time

import pytest

from ladon.proof_contract_rational_probes import (
    RATIONAL_BRANCH_PROFILE_DIGEST,
    plan_rational_branch_probe,
)
from ladon.proof_contract_refinement import (
    check_rational_refinement,
    create_refinement_branch,
)
from ladon.proofir_v3 import (
    ProofIRV3Error,
    detached_content_id,
    validate_envelope,
)
from ladon.rational_lean import encode_rational_goal

SOURCE_ROOT = "/home/codex/projects/ladon"
WORKSPACE_ROOT = "/home/codex/projects/lean/matrix-factorization"
LIMITS = {
    "timeout_seconds": 30,
    "max_output_bytes": 8 * 1024 * 1024,
    "max_rss_bytes": 12 * 1024**3,
}


def _finding():
    return {
        "id": "finding-plan-red",
        "status": "abstract-countermodel",
        "discrepancy": {"claim": "x is nonnegative", "observed": "x = -1"},
        "witness": {"id": "witness-plan-red", "assignment": {"x": "-1"}},
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


def _branch(expression=None, *, source_root=SOURCE_ROOT):
    constraint = {
        "id": "repair-nonnegative-domain",
        "expression": _predicate() if expression is None else expression,
        "justification": {
            "kind": "proposed-repair",
            "rationale": "Try restricting the domain to nonnegative inputs.",
        },
    }
    return create_refinement_branch(_finding(), [constraint], source_root=source_root)


def _request(branch=None, base=None, assignment=None, *, source_root=SOURCE_ROOT, workspace_root=WORKSPACE_ROOT):
    return {
        "sourceRoot": source_root,
        "workspaceRoot": workspace_root,
        "branch": _branch() if branch is None else branch,
        "baseGoal": _goal() if base is None else base,
        "assignment": {"x": "1"} if assignment is None else assignment,
        "deadlineMonotonic": time.monotonic() + 60,
        "limits": copy.deepcopy(LIMITS),
    }


def _identity(plan):
    return plan["planId"]


def test_request_is_closed_and_rejects_caller_lean_or_goal_text():
    request = _request()
    plan_rational_branch_probe(request)

    for field, value in (
        ("goal", "by trivial"),
        ("leanGoal", "True"),
        ("lean", "import Mathlib"),
        ("proof", "by norm_num"),
        ("proofTerm", "by norm_num"),
    ):
        forged = copy.deepcopy(request)
        forged[field] = value
        with pytest.raises((TypeError, ValueError)):
            plan_rational_branch_probe(forged)


def test_plan_identity_is_stable_recomputed_and_binds_semantic_inputs():
    request = _request()
    first = plan_rational_branch_probe(request)
    repeated = plan_rational_branch_probe(copy.deepcopy(request))
    assert _identity(first) == _identity(repeated)

    variants = []
    other_branch = _branch(_predicate("gt", right={"rat": "-1"}))
    variants.append(_request(branch=other_branch))
    variants.append(_request(base=_goal(conclusion=_predicate("gt"))))
    variants.append(_request(assignment={"x": "2"}))
    for changed in variants:
        assert _identity(plan_rational_branch_probe(changed)) != _identity(first)


def _assert_plan_schema_and_status(plan):
    assert plan["schema"] == "ladon-rational-branch-plan-v1"
    assert plan["status"] == "planned"


def _assert_plan_branch_binding(plan, checked):
    assert plan["branchId"] == checked["branchId"]
    assert plan["branchKind"] == checked["branchKind"]


def _assert_plan_goal_bindings(plan, checked):
    assert plan["baseGoal"] == checked["baseGoal"]
    assert plan["baseGoalSha256"] == checked["baseGoalSha256"]
    assert plan["derivedGoal"] == checked["derivedGoal"]
    assert plan["derivedGoalSha256"] == checked["derivedGoalSha256"]
    assert plan["assignment"] == checked["assignment"]


def _assert_plan_matches_encoded_goals(plan, expected_encoding):
    assert plan["checkerIdentity"] == expected_encoding["checkerIdentity"]
    assert plan["goals"] == expected_encoding["obligations"]
    assert plan["generatedGoalIdentities"] == [
        goal["goalId"] for goal in plan["goals"]
    ]


def test_plan_regenerates_exact_branch_base_assignment_and_goals():
    request = _request()
    checked = check_rational_refinement(
        request["branch"], request["baseGoal"], request["assignment"],
        source_root=request["sourceRoot"],
    )
    expected_encoding = encode_rational_goal(
        checked["derivedGoal"], request["assignment"]
    )

    plan = plan_rational_branch_probe(request)

    _assert_plan_schema_and_status(plan)
    _assert_plan_branch_binding(plan, checked)
    _assert_plan_goal_bindings(plan, checked)
    _assert_plan_matches_encoded_goals(plan, expected_encoding)


def test_plan_preserves_source_fidelity_and_finite_scope_nonclaims():
    plan = plan_rational_branch_probe(_request())

    assert plan["sourceFormulaFidelity"] == "unverified"
    assert plan["originalClaimRefuted"] is False
    nonclaims = " ".join(plan["nonclaims"]).lower()
    assert "source formula fidelity" in nonclaims
    assert "finite assignment" in nonclaims or "universal" in nonclaims
    assert "checked support" not in plan
    assert "receipt" not in plan


def test_zero_division_is_rejected_before_goal_generation():
    branch = _branch({
        "op": "ge",
        "left": {
            "op": "div",
            "args": [{"rat": "1"}, {"rat": "0"}],
        },
        "right": {"rat": "0"},
    })

    result = plan_rational_branch_probe(_request(branch=branch))

    assert result["status"] in {"rejected", "unsupported"}
    assert result.get("goals", []) == []
    assert result.get("generatedGoalIdentities", []) == []
    assert result.get("checkedSupport") is None


def test_missing_mathlib_is_unsupported_without_goals_or_checking(tmp_path):
    branch = _branch()
    result = plan_rational_branch_probe(
        _request(branch=branch, workspace_root=str(tmp_path))
    )

    assert result["status"] == "unsupported"
    assert result.get("goals", []) == []
    assert result.get("generatedGoalIdentities", []) == []
    assert result.get("checkedSupport") is None
    assert result.get("receipt") is None


def test_workspace_root_is_bound_separately_from_source_root_and_branch(tmp_path):
    request = _request()
    original_source_root = request["sourceRoot"]
    original_branch = copy.deepcopy(request["branch"])
    first = plan_rational_branch_probe(request)

    changed_workspace = copy.deepcopy(request)
    changed_workspace["workspaceRoot"] = str(tmp_path)
    second = plan_rational_branch_probe(changed_workspace)

    assert changed_workspace["sourceRoot"] == original_source_root
    assert changed_workspace["branch"] == original_branch
    if first.get("planId") is not None and second.get("planId") is not None:
        assert first["planId"] != second["planId"]
    else:
        assert first.get("workspaceIdentity") is not None
        assert second.get("workspaceIdentity") is not None
        assert first["workspaceIdentity"] != second["workspaceIdentity"]


def _assert_validated_rational_analysis_artifact(plan, artifact):
    validated = validate_envelope(artifact)
    assert validated.to_dict() == artifact
    assert artifact["artifactKind"] == "proofir.contract-analysis"
    assert artifact["environmentRef"] == plan["workspaceIdentity"]


def _assert_rational_analysis_payload(plan, artifact):
    payload = artifact["payload"]
    assert payload["stage"] == "rational-branch"
    assert payload["result"] == {key: value for key, value in plan.items() if key != "artifact"}
    assert payload["profileDigest"] == RATIONAL_BRANCH_PROFILE_DIGEST
    assert {"kind": "contract-analysis", "localId": payload["analysisId"]} in artifact["subjectRefs"]


def _assert_rational_analysis_limitations(artifact):
    limitation_text = " ".join(
        limitation["message"].lower() for limitation in artifact["limitations"]
    )
    assert "source formula fidelity" in limitation_text
    assert "finite assignment" in limitation_text or "universal" in limitation_text


def test_successful_plan_is_owned_by_validated_rational_branch_envelope():
    plan = plan_rational_branch_probe(_request())

    artifact = plan["artifact"]
    _assert_validated_rational_analysis_artifact(plan, artifact)
    _assert_rational_analysis_payload(plan, artifact)
    _assert_rational_analysis_limitations(artifact)


def _reidentify_artifact(artifact):
    artifact["artifactId"] = detached_content_id(artifact)
    return artifact


@pytest.mark.parametrize("mutation", ["tampered-stage", "unexpected-key"])
def test_native_validation_rejects_reidentified_rational_analysis_tampering(mutation):
    artifact = copy.deepcopy(plan_rational_branch_probe(_request())["artifact"])
    if mutation == "tampered-stage":
        artifact["payload"]["stage"] = "rational-branch-tampered"
    else:
        artifact["payload"]["unexpected"] = True
    _reidentify_artifact(artifact)

    with pytest.raises(ProofIRV3Error):
        validate_envelope(artifact)


def _matrix_goal():
    x = {"var": "x"}
    two = {"rat": "2"}
    zero = {"rat": "0"}
    four = {"rat": "4"}
    one = {"rat": "1"}
    three = {"rat": "3"}
    return _goal(
        premises=[
            _predicate("eq", {"op": "add", "args": [one, one]}, two),
            _predicate("eq", {"op": "sub", "args": [x, two]}, zero),
            _predicate("eq", {"op": "mul", "args": [x, two]}, four),
            _predicate("eq", {"op": "div", "args": [x, two]}, one),
            _predicate("lt", {"op": "neg", "args": [x]}, zero),
            _predicate("eq", {"op": "abs", "args": [{"op": "neg", "args": [x]}]}, two),
            _predicate("gt", {"op": "pow", "args": [x], "exponent": 2}, three),
            _predicate("le", x, one),  # false at the equality boundary x=2
            _predicate("ne", x, two),  # false at equality
            _predicate("ge", x, two),  # true at equality
            _predicate("lt", x, two),  # strict comparison is false at equality
        ],
        conclusion=_predicate("gt", x, two),
    )


def test_combined_rational_matrix_matches_python_and_passes_lean_preflight():
    request = _request(base=_matrix_goal(), assignment={"x": "2"})
    checked = check_rational_refinement(
        request["branch"], request["baseGoal"], request["assignment"],
        source_root=request["sourceRoot"],
    )
    expected_encoding = encode_rational_goal(
        checked["derivedGoal"], request["assignment"]
    )

    plan = plan_rational_branch_probe(request)

    assert plan["status"] == "planned"
    assert plan["leanPreflightStatus"] == "passed"
    assert plan["goals"] == expected_encoding["obligations"]
    python_holds = [row["holds"] for row in checked["witnessCheck"]["premises"]]
    python_holds.append(checked["witnessCheck"]["conclusion"]["holds"])
    expected_holds = [goal["expectedHolds"] for goal in plan["goals"]]
    assert expected_holds == python_holds
    assert expected_holds == [
        True, True, True, True, True, True, True,
        False, False, True, False, True, False,
    ]
    assert validate_envelope(plan["artifact"]).to_dict() == plan["artifact"]
