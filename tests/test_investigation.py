"""Red contract proposal for the correspondence investigation loop.

These tests intentionally target only the public controller and CLI surfaces.
They do not assert mathematical correctness of authored contracts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from ladon.investigation import assess
from ladon.investigation_cli import investigation_main

CONTRACT_FIELDS = {
    "objects": "source assertion",
    "assumptions": "the stated local assumptions",
    "domains": "the stated domain",
    "quantifiers": "the stated quantifiers",
    "conclusion": "the stated conclusion",
    "dependencies": "the cited local facts",
    "neededImplication": "the implication needed for the next step",
}


@pytest.fixture
def case(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("For every x, x equals x.\n", encoding="utf-8")
    now = datetime.now(UTC)

    def plan(
        *,
        started_at=None,
        budget=90 * 60,
        unit_state="pending",
        claim_state="captured",
        local_contract=None,
        formal=None,
        judgment=None,
        blocker=None,
    ):
        claim = {
            "id": "claim-1",
            "unit": "unit-1",
            "startLine": 1,
            "endLine": 1,
            "quote": "For every x, x equals x.",
            "state": claim_state,
        }
        if local_contract is not None:
            claim["contract"] = local_contract
        if formal is not None:
            claim["formal"] = formal
        if judgment is not None:
            claim["judgment"] = judgment
        if blocker is not None:
            claim["blocker"] = blocker
        return {
            "version": 1,
            "startedAt": (started_at or now).isoformat().replace("+00:00", "Z"),
            "budgetSeconds": budget,
            "scope": {
                "path": "source.txt",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "startLine": 1,
                "endLine": 1,
            },
            "units": [
                {
                    "id": "unit-1",
                    "startLine": 1,
                    "endLine": 1,
                    "inventory": unit_state,
                    **(
                        {"note": "Inventory recorded for this source unit."}
                        if unit_state == "done"
                        else {}
                    ),
                }
            ],
            "claims": [claim],
        }

    return {"root": tmp_path, "source": source, "now": now, "plan": plan}


def _formal_record():
    return {
        "path": "source.txt",
        "sha256": "unused-until-bound-to-formal-source",
        "startLine": 1,
        "endLine": 1,
        "statement": "For every x, x equals x.",
        "contract": dict(CONTRACT_FIELDS),
    }


def _bound_review(case, *, statement="unresolved", method="same"):
    formal = _formal_record()
    formal["sha256"] = hashlib.sha256(case["source"].read_bytes()).hexdigest()
    return (
        dict(CONTRACT_FIELDS),
        formal,
        {
            "statement": statement,
            "method": method,
            "evidence": "The local comparison record leaves this judgment unresolved.",
        },
    )


def _tasks(result):
    """Read the public next-batch list while keeping assertions about work exact."""
    return result["next"]


def _contains(value, target):
    if value == target:
        return True
    if isinstance(value, dict):
        return any(_contains(item, target) for item in value.values())
    if isinstance(value, list):
        return any(_contains(item, target) for item in value)
    return False


def test_finish_rejects_early_stop_at_fifteen_of_ninety_minutes(case, tmp_path, capsys):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            case["plan"](
                started_at=case["now"] - timedelta(minutes=15),
            )
        ),
        encoding="utf-8",
    )

    exit_code = investigation_main(
        [
            "finish",
            "--plan",
            str(plan_path),
            "--root",
            str(case["root"]),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["status"] == "continue"
    assert output["mayFinalize"] is False
    assert _tasks(output), "finish must return the next useful work before the deadline"


def test_captured_claim_without_exact_contract_stays_actionable(case):
    result = assess(case["plan"](unit_state="done"), case["root"], now=case["now"])

    assert result["mayFinalize"] is False
    assert any(item.get("kind") == "write-exact-contract" for item in _tasks(result))


def test_reviewed_but_unresolved_step_stays_actionable(case):
    local, formal, judgment = _bound_review(case)
    result = assess(
        case["plan"](
            unit_state="done",
            claim_state="reviewed",
            local_contract=local,
            formal=formal,
            judgment=judgment,
        ),
        case["root"],
        now=case["now"],
    )

    assert result["mayFinalize"] is False
    assert any(item.get("kind") == "resolve-local-obligation" for item in _tasks(result))


def test_exhausted_budget_exits_as_explicitly_incomplete(case, tmp_path, capsys):
    plan_path = tmp_path / "plan.json"
    old_start = case["now"] - timedelta(minutes=91)
    plan_path.write_text(json.dumps(case["plan"](started_at=old_start)), encoding="utf-8")

    exit_code = investigation_main(
        [
            "finish",
            "--plan",
            str(plan_path),
            "--root",
            str(case["root"]),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "incomplete-budget"
    assert output["mayFinalize"] is True
    assert output["next"] or output["blocked"], "budget stop must preserve remaining obligations"


def test_evidenced_blocker_exits_as_incomplete_blocked(case, tmp_path, capsys):
    blocked_claim = {
        "kind": "missing-local-source",
        "evidence": "The cited local declaration is absent from the bounded source.",
        "nextAction": "Request the missing source excerpt.",
        "unblockCondition": "The exact referenced source span is supplied.",
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            case["plan"](
                unit_state="done",
                claim_state="blocked",
                blocker=blocked_claim,
            )
        ),
        encoding="utf-8",
    )

    exit_code = investigation_main(
        [
            "finish",
            "--plan",
            str(plan_path),
            "--root",
            str(case["root"]),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "incomplete-blocked"
    assert output["mayFinalize"] is True
    assert _contains(output, blocked_claim), "final result must preserve blocker details"


def test_blocked_claim_does_not_hide_actionable_work_before_deadline(case):
    blocked_claim = {
        "kind": "missing-local-source",
        "evidence": "The cited local declaration is absent from the bounded source.",
        "nextAction": "Request the missing source excerpt.",
        "unblockCondition": "The exact referenced source span is supplied.",
    }
    plan = case["plan"](unit_state="done", claim_state="blocked", blocker=blocked_claim)
    plan["claims"].append(
        {
            **plan["claims"][0],
            "id": "claim-2",
            "state": "captured",
        }
    )
    result = assess(plan, case["root"], now=case["now"])

    assert result["status"] == "continue"
    assert result["mayFinalize"] is False
    assert any(
        item.get("kind") == "write-exact-contract" and "claim-2" in json.dumps(item)
        for item in _tasks(result)
    )
    assert _contains(result, blocked_claim), (
        "blocked details must remain visible alongside actionable work"
    )


def _change_invalid_record(case, plan, change):
    if change == "digest":
        case["source"].write_text("Changed source.\n")
    elif change == "quote":
        plan["claims"][0]["quote"] = "Invented assertion"
    elif change == "gap":
        plan["units"] = []
    elif change == "overlap":
        plan["units"].append({**plan["units"][0], "id": "unit-2"})
    elif change == "duplicate":
        plan["claims"].append(dict(plan["claims"][0]))
    elif change == "boolean":
        plan["budgetSeconds"] = True
    else:
        _change_temporal_or_contract_record(case, plan, change)


def _change_temporal_or_contract_record(case, plan, change):
    if change == "future":
        plan["startedAt"] = (case["now"] + timedelta(seconds=1)).isoformat()
    elif change == "naive":
        plan["startedAt"] = case["now"].replace(tzinfo=None).isoformat()
    elif change == "blocker":
        plan["claims"][0].update(state="blocked", blocker={"kind": "unavailable"})
    elif change == "contract":
        plan["claims"][0].update(state="contract", contract={"objects": "x"})



@pytest.mark.parametrize(
    "change",
    [
        "digest",
        "quote",
        "gap",
        "overlap",
        "duplicate",
        "boolean",
        "future",
        "naive",
        "blocker",
        "contract",
    ],
)
def test_invalid_records_reject(case, change):
    plan = case["plan"](unit_state="done")
    _change_invalid_record(case, plan, change)
    with pytest.raises(ValueError):
        assess(plan, case["root"], now=case["now"])


@pytest.mark.parametrize("symlink", [False, True])
def test_outside_source_rejected(case, symlink):
    outside = case["root"].parent / (case["root"].name + "-outside.txt")
    outside.write_bytes(case["source"].read_bytes())
    plan = case["plan"]()
    if symlink:
        (case["root"] / "escape.txt").symlink_to(outside)
        plan["scope"]["path"] = "escape.txt"
    else:
        plan["scope"]["path"] = "../" + outside.name
    with pytest.raises(ValueError, match="escapes"):
        assess(plan, case["root"], now=case["now"])


def test_completed_record_is_only_bookkeeping(case):
    local, formal, judgment = _bound_review(case, statement="aligned")
    result = assess(
        case["plan"](
            unit_state="done",
            claim_state="reviewed",
            local_contract=local,
            formal=formal,
            judgment=judgment,
        ),
        case["root"],
        now=case["now"],
    )
    assert result["status"] == "recorded-work-complete"
    assert result["counts"]["reviewedClaims"] == 1
    assert "No mathematical truth" in result["nonclaims"][0]


def test_duplicate_json_keys_rejected(tmp_path):
    from ladon.investigation import load_plan

    path = tmp_path / "duplicate.json"
    path.write_text('{"version":1,"version":1}')
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_plan(path)


def test_source_and_plan_bounds(tmp_path, monkeypatch):
    import ladon.investigation as controller

    source = tmp_path / "large.txt"
    source.write_text("abcdef\n")
    monkeypatch.setattr(controller, "MAX_SOURCE_BYTES", 4)
    with pytest.raises(ValueError, match="source exceeds"):
        controller.initialize(source, tmp_path)
    monkeypatch.setattr(controller, "MAX_PLAN_BYTES", 4)
    with pytest.raises(ValueError, match="plan exceeds"):
        controller.load_plan(source)
