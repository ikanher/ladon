"""Discrepancy priority, challenge integrity and exact-witness consumer regressions."""

from __future__ import annotations

import copy
import json

import pytest

from ladon.investigation import CONTRACT_FIELDS, assess, initialize, step_subject
from ladon.investigation_cli import investigation_main
from ladon.rational_witness import check_witness, validate_goal


def rat(x):
    return {"rat": x}


def pred(op, lhs, rhs):
    return {"op": op, "left": lhs, "right": rhs}


def goal():
    return {
        "variables": ["x"],
        "premises": [pred("gt", {"var": "x"}, rat(0))],
        "conclusion": pred("ge", {"var": "x"}, rat(1)),
    }


@pytest.fixture
def case(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("Earlier material.\nOther material.\nPositive x is at least one.\n")
    plan = initialize(source, tmp_path, derivations=True, unit_lines=1)
    contract = {field: "Explicit " + field for field in CONTRACT_FIELDS}
    claim = {
        "id": "gap",
        "unit": plan["units"][2]["id"],
        "startLine": 3,
        "endLine": 3,
        "quote": "Positive x is at least one.",
        "state": "contract",
        "contract": contract,
        "concern": "Check the claimed implication.",
    }
    plan["claims"] = [claim]
    step = {
        "id": "s1",
        "startLine": 3,
        "endLine": 3,
        "quote": claim["quote"],
        "contract": copy.deepcopy(contract),
        "rule": "Order inference",
        "substitution": "x denotes the original positive rational.",
        "dependsOn": [],
        "arithmetic": goal(),
        "assessment": {"outcome": "supported", "evidence": "Author review."},
    }
    claim["derivation"] = {"author": "author", "steps": [step]}
    return plan, claim, step, tmp_path


def challenge(plan, claim, step, **changes):
    return {
        "reviewer": "challenger",
        "subjectSha256": step_subject(plan, claim, step),
        "outcome": "supported",
        "evidence": "Independent conventional argument.",
        **changes,
    }


def test_step_challenge_precedes_unexamined_inventory(case):
    plan, claim, step, root = case
    result = assess(plan, root)
    assert result["next"][0]["kind"] == "challenge-step"
    assert result["next"][0]["claim"] == "gap"
    assert any(x["kind"] == "inventory-source" for x in result["next"])
    step["challenge"] = challenge(plan, claim, step, outcome="unresolved")
    assert assess(plan, root)["next"][0]["kind"] == "reconcile-step"


@pytest.mark.parametrize(
    "statement,method",
    [
        ("mismatch", "same"),
        ("aligned", "different"),
        ("unresolved", "same"),
        ("aligned", "unresolved"),
    ],
)
def test_correspondence_discrepancies_require_steps_without_explicit_concern(
    case, statement, method
):
    plan, claim, _step, root = case
    del claim["concern"], claim["derivation"]
    claim.update(
        state="reviewed",
        formal={
            **plan["scope"],
            "startLine": 3,
            "endLine": 3,
            "statement": claim["quote"],
            "contract": claim["contract"],
        },
        judgment={"statement": statement, "method": method, "evidence": "Attributed comparison."},
    )
    assert assess(plan, root)["next"][0]["kind"] == "decompose-derivation"


def test_blocked_gap_does_not_hide_unexamined_work(case):
    plan, claim, _step, root = case
    claim.update(
        state="blocked",
        blocker={
            "kind": "unavailable",
            "evidence": "Specific missing source.",
            "nextAction": "Acquire source.",
            "unblockCondition": "Source supplied.",
        },
    )
    result = assess(plan, root)
    assert result["status"] == "continue"
    assert result["blocked"][0]["claim"] == "gap"
    assert result["next"][0]["kind"] == "inventory-source"


def test_stale_predecessor_and_same_reviewer_rejected(case):
    plan, claim, step, root = case
    second = copy.deepcopy(step)
    second.update(id="s2", dependsOn=["s1"])
    claim["derivation"]["steps"].append(second)
    second["challenge"] = challenge(plan, claim, second)
    step["contract"]["assumptions"] = "Different premise"
    with pytest.raises(ValueError, match="stale challenge"):
        assess(plan, root)
    second["challenge"] = challenge(plan, claim, second, reviewer=" author ")
    with pytest.raises(ValueError, match="different reviewer"):
        assess(plan, root)


def test_real_counterexample_cannot_be_hidden_by_supported_labels(case):
    plan, claim, step, root = case
    step["challenge"] = challenge(plan, claim, step, witness={"x": "1/2"})
    result = assess(plan, root)
    assert result["next"][0]["kind"] == "reconcile-step"
    assert result["findings"][0]["check"]["status"] == "counterexample"
    step["challenge"]["outcome"] = "refuted"
    step["challenge"]["witness"] = {"x": "-1"}
    with pytest.raises(ValueError, match="does not refute"):
        assess(plan, root)


def _export_sanitized_packet(plan, claim, step, root, capsys):
    plan["scope"]["repair"] = "SECRET_SCOPE_REPAIR"
    claim["repair"] = "SECRET_CLAIM_REPAIR"
    step["repair"] = "SECRET_STEP_REPAIR"
    step["assessment"]["evidence"] = "SECRET_ASSESSMENT"
    step["contract"]["priorJudgment"] = "SECRET_CONTRACT_METADATA"
    step["challenge"] = challenge(plan, claim, step, evidence="SECRET_CHALLENGE")
    path = root / "plan.json"
    path.write_text(json.dumps(plan))
    before = path.read_bytes()
    output = root / "packet.json"
    assert (
        investigation_main(
            [
                "challenge",
                "--plan",
                str(path),
                "--root",
                str(root),
                "--claim",
                "gap",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert "SECRET" not in output.read_text()
    packet = json.loads(output.read_text())
    assert packet["steps"][0]["subjectSha256"] == step_subject(plan, claim, step)
    assert packet["steps"][0]["arithmetic"] == goal()
    assert (
        investigation_main(
            [
                "challenge",
                "--plan",
                str(path),
                "--root",
                str(root),
                "--claim",
                "gap",
                "--output",
                str(output),
            ]
        )
        == 2
    )
    capsys.readouterr()
    return path, before, packet


def test_sanitized_export_and_stored_goal_cli_replay(case, capsys):
    plan, claim, step, root = case
    path, before, packet = _export_sanitized_packet(plan, claim, step, root, capsys)
    assignment = root / "assignment.json"
    assignment.write_text('{"x":"1/2"}')
    assert (
        investigation_main(
            [
                "witness",
                "--plan",
                str(path),
                "--root",
                str(root),
                "--claim",
                "gap",
                "--step",
                "s1",
                "--assignment",
                str(assignment),
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "counterexample"
    assert result["subjectSha256"] == packet["steps"][0]["subjectSha256"]
    assert path.read_bytes() == before
    assignment.write_text(json.dumps({"x": "1/2", "goal": goal()}))
    assert (
        investigation_main(
            [
                "witness",
                "--plan",
                str(path),
                "--root",
                str(root),
                "--claim",
                "gap",
                "--step",
                "s1",
                "--assignment",
                str(assignment),
            ]
        )
        == 2
    )


def test_cycle_or_outside_span_rejected(case):
    plan, _claim, step, root = case
    step["dependsOn"] = ["s1"]
    with pytest.raises(ValueError, match="earlier step"):
        assess(plan, root)
    step["dependsOn"] = []
    step["startLine"] = 2
    with pytest.raises(ValueError, match="inside claim"):
        assess(plan, root)


@pytest.mark.parametrize("literal", [10**128, -(10**127), "1/0", "1.0", True, 1.5])
def test_literal_bounds(literal):
    with pytest.raises(ValueError):
        check_witness(goal(), {"x": literal})


def test_arithmetic_depth_nodes_and_intermediate_limits():
    expr = rat(1)
    for _ in range(33):
        expr = {"op": "neg", "args": [expr]}
    g = {"variables": [], "premises": [], "conclusion": pred("eq", expr, rat(1))}
    with pytest.raises(ValueError, match="depth"):
        validate_goal(g)
    expr = rat(1)
    for _ in range(12):
        expr = {"op": "add", "args": [expr, expr]}
    g["conclusion"] = pred("eq", expr, rat(1))
    with pytest.raises(ValueError, match="nodes"):
        validate_goal(g)
    expr = {
        "op": "pow",
        "args": [{"op": "pow", "args": [rat(10**100)], "exponent": 8}],
        "exponent": 8,
    }
    g["conclusion"] = pred("eq", expr, rat(1))
    with pytest.raises(ValueError, match="bits"):
        check_witness(g, {})


def test_sample_success_is_not_a_proof_and_rational_values_are_exact():
    result = check_witness(goal(), {"x": "5/3"})
    assert result["status"] == "not-counterexample"
    assert result["conclusion"]["lhs"] == "5/3"
    assert any("universal" in s for s in result["nonclaims"])
