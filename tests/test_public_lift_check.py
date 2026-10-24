"""Black-box red contract for the source-owned Nat/rational lift checker.

It intentionally does not prescribe the supervised worker JSON protocol.
"""

from __future__ import annotations

import hashlib
import inspect
import time
from pathlib import Path

import pytest

from ladon.proof_contract_lift_check import check_nat_rational_lift
from ladon.proof_contract_lift_goals import plan_nat_rational_lift

GOAL = {
    "variables": ["x"],
    "premises": [],
    "conclusion": {"op": "eq", "left": {"var": "x"}, "right": {"rat": 0}},
}
WITNESS = {
    "id": "w-lift-check",
    "status": "abstract-countermodel",
    "assignment": {"x": "1"},
}


def _source(
    tmp_path: Path,
    content: str = "namespace Fixture\ndef predicate (_n : Nat) : Prop := True\ntheorem claim : True := trivial\nend Fixture\n",
):
    path = tmp_path / "Fixture" / "Lift.lean"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    interpretation = {
        "profile": "nat-cast-v1",
        "source": {"path": "Fixture/Lift.lean", "sha256": digest},
        "formalClaim": "Fixture.claim",
        "formalPredicate": "Fixture.predicate",
    }
    return path, interpretation


def _request(
    tmp_path: Path,
    interpretation: dict,
    *,
    goal: dict = GOAL,
    witness: dict = WITNESS,
    mode: str = "realization",
    **extra,
):
    return {
        "repoRoot": str(tmp_path),
        "goal": goal,
        "witness": witness,
        "interpretation": interpretation,
        "mode": mode,
        "deadlineMonotonic": time.monotonic() + 30,
        "limits": {},
        **extra,
    }


def _plan(goal, witness, interpretation, mode):
    return plan_nat_rational_lift(goal, witness, interpretation, mode=mode)


def _assert_nonpositive_result(result, witness):
    assert result["status"] in {
        "rejected",
        "stale-input",
        "unsupported",
        "incomplete",
        "unresolved",
    }
    assert result["witness"] == witness
    assert result["originalClaimRefuted"] is False
    assert result["formalClaimRefuted"] is False
    assert result["spuriousnessEvidence"] is None
    assert result["realizationEvidence"] is None
    assert result["checkId"] is None


def _patch_process_spawn(monkeypatch):
    """Fail if a rejection/unsupported case attempts any subprocess."""
    import subprocess

    def forbidden(*_args, **_kwargs):
        pytest.fail("checker launched a subprocess before request freshness/eligibility passed")

    monkeypatch.setattr(subprocess, "Popen", forbidden)


def test_public_signature_has_only_owned_request_plan_id_and_term():
    parameters = list(inspect.signature(check_nat_rational_lift).parameters)
    assert parameters == ["request", "plan_id", "term"]


@pytest.mark.parametrize(
    "extra",
    [
        {"cache": {}},
        {"receipt": {"status": "accepted"}},
        {"runner": lambda *_a, **_k: None},
    ],
)
def test_arbitrary_checker_authority_arguments_are_rejected_without_execution(
    tmp_path, monkeypatch, extra
):
    _, interpretation = _source(tmp_path)
    request = _request(tmp_path, interpretation)
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    _patch_process_spawn(monkeypatch)

    with pytest.raises(TypeError):
        check_nat_rational_lift(request, planned["planId"], "by trivial", **extra)


def test_extra_request_authority_fields_are_rejected_before_execution(tmp_path, monkeypatch):
    _, interpretation = _source(tmp_path)
    request = _request(tmp_path, interpretation, cache={"positive": True})
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_nonpositive_result(result, WITNESS)


def test_unsupported_plan_is_reported_without_native_execution(tmp_path, monkeypatch):
    _, interpretation = _source(tmp_path)
    divided_goal = {
        "variables": ["x"],
        "premises": [],
        "conclusion": {
            "op": "eq",
            "left": {"op": "div", "args": [{"var": "x"}, {"rat": 1}]},
            "right": {"rat": 0},
        },
    }
    # Use the planner's accepted expression shape, then require its unsupported plan
    # to stay a native no-op. (The exact valid unsupported AST is refined at integration.)
    planned = _plan(divided_goal, WITNESS, interpretation, "realization")
    assert planned["status"] == "unsupported"
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(
        _request(tmp_path, interpretation, goal=divided_goal), planned["planId"], None
    )

    _assert_nonpositive_result(result, WITNESS)
    assert result["status"] == "unsupported"


@pytest.mark.parametrize("stale_kind", ["plan", "source"])
def test_stale_plan_or_source_is_rejected_before_native_execution(
    tmp_path, monkeypatch, stale_kind
):
    source, interpretation = _source(tmp_path)
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    request = _request(tmp_path, interpretation)
    plan_id = planned["planId"]
    if stale_kind == "plan":
        plan_id = "sha256:" + "0" * 64
    else:
        source.write_text(
            source.read_text(encoding="utf-8") + "-- changed after planning\n", encoding="utf-8"
        )
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(request, plan_id, "by trivial")

    _assert_nonpositive_result(result, WITNESS)
    assert result["status"] == "stale-input"


def test_expired_absolute_deadline_is_incomplete_and_preserves_witness(tmp_path, monkeypatch):
    _, interpretation = _source(tmp_path)
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    request = _request(tmp_path, interpretation)
    request["deadlineMonotonic"] = time.monotonic() - 1
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_nonpositive_result(result, WITNESS)
    assert result["status"] == "incomplete"
    assert result["diagnostic"]


@pytest.mark.parametrize(
    "limits",
    [
        {"timeout_seconds": -1},
        {"max_output_bytes": 8 * 1024 * 1024 + 1},
        {"max_rss_bytes": True},
        {"runner": "caller-controlled"},
    ],
)
def test_invalid_resource_controls_are_nonpositive(tmp_path, monkeypatch, limits):
    _, interpretation = _source(tmp_path)
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    request = _request(tmp_path, interpretation)
    request["limits"] = limits
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_nonpositive_result(result, WITNESS)
    assert result["diagnostic"]


def test_invalid_source_does_not_mutate_filesystem_or_return_positive_flags(tmp_path, monkeypatch):
    source, interpretation = _source(tmp_path)
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    source.write_bytes(b"\xff")
    before_after_tamper = {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(
        _request(tmp_path, interpretation), planned["planId"], "by trivial"
    )

    _assert_nonpositive_result(result, WITNESS)
    assert result["status"] in {"rejected", "stale-input"}
    assert {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == before_after_tamper
    assert before  # fixture sanity: source exists and the check is observation-only


def test_public_result_never_promotes_caller_supplied_positive_flags(tmp_path, monkeypatch):
    _, interpretation = _source(tmp_path)
    request = _request(
        tmp_path,
        interpretation,
        formalClaimRefuted=True,
        sourceVerified=True,
        realizationEvidence={"checkId": "forged"},
    )
    planned = _plan(GOAL, WITNESS, interpretation, "realization")
    _patch_process_spawn(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_nonpositive_result(result, WITNESS)


# Positive proof cases belong in the integrated public-API native gate. At unit level,
# worker response binding/freshness and fake accepted capture/completion/replay/trust
# receipts are intentionally left to tests at the settled internal boundary; inventing
# that private response wire would couple this independent red suite to implementation.
