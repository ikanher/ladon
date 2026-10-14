"""Executable public-contract red tests; never assert source-claim truth."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest


def _predicate(op, left, right):
    return {"op": op, "left": left, "right": right}


def _rat(value):
    return {"rat": value}


def test_rational_witness_classifies_exact_counterexample_and_wrong_premise():
    from ladon.rational_witness import check_witness

    goal = {
        "variables": ["x"],
        "premises": [_predicate("gt", {"var": "x"}, _rat(0))],
        "conclusion": _predicate("ge", {"var": "x"}, _rat(1)),
    }
    checked = check_witness(goal, {"x": "1/2"})
    assert checked["schema"] == "ladon-rational-witness-v1"
    assert checked["status"] == "counterexample"
    assert checked["premises"][0]["holds"] is True
    assert checked["conclusion"]["holds"] is False
    assert checked["premises"][0]["lhs"] == "1/2"

    wrong_premise = check_witness(goal, {"x": "-1"})
    assert wrong_premise["status"] == "outside-assumptions"
    assert wrong_premise["premises"][0]["holds"] is False


def test_rational_witness_rejects_bool_float_extra_binding_and_division_by_zero():
    from ladon.rational_witness import check_witness

    goal = {
        "variables": ["x"],
        "premises": [],
        "conclusion": _predicate("eq", {"var": "x"}, _rat(0)),
    }
    for bad_assignment in ({"x": True}, {"x": 0.5}, {"x": 0, "y": 1}):
        with pytest.raises(ValueError):
            check_witness(goal, bad_assignment)

    divided = {
        "variables": ["x"],
        "premises": [_predicate("eq", {"op": "div", "args": [{"var": "x"}, _rat(0)]}, _rat(0))],
        "conclusion": _predicate("eq", {"var": "x"}, _rat(0)),
    }
    with pytest.raises(ValueError):
        check_witness(divided, {"x": 0})


def test_full_goal_validation_does_not_short_circuit_after_false_premise():
    from ladon.rational_witness import check_witness

    malformed_later = {"op": "wat", "args": [_rat(0), _rat(1)]}
    goal = {
        "variables": ["x"],
        "premises": [
            _predicate("lt", {"var": "x"}, _rat(0)),
            _predicate("eq", malformed_later, _rat(1)),
        ],
        "conclusion": _predicate("eq", _rat(0), _rat(0)),
    }
    with pytest.raises(ValueError):
        check_witness(goal, {"x": 1})


def test_initialize_derivations_is_opt_in_and_assess_keeps_v1_compatible(tmp_path):
    from ladon.investigation import assess, initialize

    source = tmp_path / "source.txt"
    source.write_text("For every x, x equals x.\n", encoding="utf-8")
    legacy = initialize(source, tmp_path, now=datetime(2026, 1, 1, tzinfo=UTC))
    modern = initialize(source, tmp_path, derivations=True, now=datetime(2026, 1, 1, tzinfo=UTC))
    assert legacy["version"] == 1
    assert modern["version"] == 2
    assert assess(legacy, tmp_path)["schema"] != "ladon-investigation-status-v2"
    assert assess(modern, tmp_path)["schema"] == "ladon-investigation-status-v2"


def test_step_subject_binds_predecessor_math_and_assessment_but_not_workflow_state(tmp_path):
    from ladon.investigation import step_subject

    base = {
        "version": 2,
        "scope": {"path": "source.txt", "sha256": "a" * 64, "startLine": 1, "endLine": 1},
        "claims": [
            {
                "id": "c",
                "unit": "u",
                "startLine": 1,
                "endLine": 1,
                "quote": "q",
                "contract": {
                    "objects": "o",
                    "assumptions": "a",
                    "domains": "d",
                    "quantifiers": "q",
                    "conclusion": "c",
                    "dependencies": "x",
                    "neededImplication": "i",
                },
                "state": "reviewed",
                "judgment": {"statement": "aligned"},
                "derivation": {
                    "author": "author",
                    "steps": [
                        {
                            "id": "s1",
                            "startLine": 1,
                            "endLine": 1,
                            "quote": "q",
                            "contract": {
                                "objects": "o",
                                "assumptions": "a",
                                "domains": "d",
                                "quantifiers": "q",
                                "conclusion": "c",
                                "dependencies": "x",
                                "neededImplication": "i",
                            },
                            "rule": "r",
                            "substitution": "s",
                            "dependsOn": [],
                            "assessment": {"outcome": "supported", "evidence": "e"},
                        },
                        {
                            "id": "s2",
                            "startLine": 1,
                            "endLine": 1,
                            "quote": "q",
                            "contract": {
                                "objects": "o",
                                "assumptions": "a",
                                "domains": "d",
                                "quantifiers": "q",
                                "conclusion": "c",
                                "dependencies": "x",
                                "neededImplication": "i",
                            },
                            "rule": "r",
                            "substitution": "s",
                            "dependsOn": ["s1"],
                        },
                    ],
                },
            }
        ],
    }
    c = base["claims"][0]
    digest = step_subject(base, c, c["derivation"]["steps"][1])
    c["state"] = "blocked"
    c["judgment"] = {"statement": "mismatch"}
    assert step_subject(base, c, c["derivation"]["steps"][1]) == digest
    c["derivation"]["steps"][0]["contract"]["assumptions"] = "changed predecessor premise"
    assert step_subject(base, c, c["derivation"]["steps"][1]) != digest


def test_suspicious_v2_claim_schedules_contract_before_decomposition(tmp_path):
    from ladon.investigation import assess, initialize

    source = tmp_path / "source.txt"
    source.write_text("Suspicious inference is stated here.\n", encoding="utf-8")
    plan = initialize(source, tmp_path, derivations=True, now=datetime(2026, 1, 1, tzinfo=UTC))
    plan["units"][0].update(inventory="done", note="Reviewed this one line.")
    plan["claims"] = [
        {
            "id": "suspicious",
            "unit": plan["units"][0]["id"],
            "startLine": 1,
            "endLine": 1,
            "quote": "Suspicious inference is stated here.",
            "state": "captured",
            "concern": "The implication is not justified.",
        }
    ]
    tasks = assess(plan, tmp_path)["next"]
    kinds = [task["kind"] for task in tasks if task.get("claim") == "suspicious"]
    assert kinds[:2] == ["write-exact-contract", "decompose-derivation"]
