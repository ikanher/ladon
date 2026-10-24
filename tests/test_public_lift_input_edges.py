"""Additional public-input edge cases for the Nat/rational lift checker.

It makes no assumptions about the private worker wire.
"""

from __future__ import annotations

import copy
import hashlib
import math
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
DIVISION_GOAL = {
    "variables": ["x"],
    "premises": [],
    "conclusion": {
        "op": "eq",
        "left": {"op": "div", "args": [{"var": "x"}, {"rat": 1}]},
        "right": {"rat": 0},
    },
}
WITNESS = {"id": "w-edge", "status": "abstract-countermodel", "assignment": {"x": "1"}}
SOURCE_TEXT = (
    "namespace Fixture\n"
    "def predicate (_n : Nat) : Prop := True\n"
    "theorem claim : True := trivial\n"
    "end Fixture\n"
)


class JsonDict(dict):
    """An object that compares equal to dict but is not exact JSON-native data."""


class JsonList(list):
    pass


def _fixture(
    tmp_path: Path, *, content: bytes = SOURCE_TEXT.encode("utf-8"), path="Fixture/Lift.lean"
):
    source = tmp_path / path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(content)
    interpretation = {
        "profile": "nat-cast-v1",
        "source": {"path": path, "sha256": hashlib.sha256(content).hexdigest()},
        "formalClaim": "Fixture.claim",
        "formalPredicate": "Fixture.predicate",
    }
    return source, interpretation


def _request(tmp_path: Path, interpretation: dict, *, goal=GOAL, **overrides):
    request = {
        "repoRoot": str(tmp_path),
        "goal": copy.deepcopy(goal),
        "witness": copy.deepcopy(WITNESS),
        "interpretation": copy.deepcopy(interpretation),
        "mode": "realization",
        "deadlineMonotonic": time.monotonic() + 30,
        "limits": {},
    }
    request.update(overrides)
    return request


def _plan(goal, interpretation):
    return plan_nat_rational_lift(goal, WITNESS, interpretation, mode="realization")


def _assert_rejected(result):
    _assert_nonpositive(result)
    assert result["status"] in {"rejected", "stale-input"}


def _assert_nonpositive(result):
    assert result["status"] in {
        "rejected",
        "stale-input",
        "unsupported",
        "incomplete",
        "unresolved",
    }
    assert result["witness"] == WITNESS
    assert result["originalClaimRefuted"] is False
    assert result["formalClaimRefuted"] is False
    assert result["spuriousnessEvidence"] is None
    assert result["realizationEvidence"] is None
    assert result["checkId"] is None


def _forbid_process(monkeypatch):
    import subprocess

    def fail(*_args, **_kwargs):
        pytest.fail("invalid public input reached a subprocess")

    monkeypatch.setattr(subprocess, "Popen", fail)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(goal=JsonDict(r["goal"])),
        lambda r: r.update(goal={**r["goal"], "variables": JsonList(r["goal"]["variables"])}),
        lambda r: r.update(deadlineMonotonic=math.nan),
        lambda r: r["interpretation"].update(formalClaim="Fixture.claim\ud800"),
    ],
)
def test_hostile_native_json_shapes_fail_closed_without_execution(tmp_path, monkeypatch, mutate):
    _, interpretation = _fixture(tmp_path)
    request = _request(tmp_path, interpretation)
    planned = _plan(GOAL, interpretation)
    mutate(request)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_rejected(result)


def test_cyclic_native_json_fails_closed_without_recursion_leak(tmp_path, monkeypatch):
    _, interpretation = _fixture(tmp_path)
    request = _request(tmp_path, interpretation)
    cycle = []
    cycle.append(cycle)
    request["goal"] = cycle
    planned = _plan(GOAL, interpretation)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_rejected(result)


@pytest.mark.parametrize("term", [None, "", 7, b"by trivial", "\ud800", "x" * (256 * 1024 + 1)])
def test_invalid_term_for_supported_plan_is_rejected_before_execution(tmp_path, monkeypatch, term):
    _, interpretation = _fixture(tmp_path)
    planned = _plan(GOAL, interpretation)
    assert planned["status"] == "planned"
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(_request(tmp_path, interpretation), planned["planId"], term)

    _assert_rejected(result)


def test_unsupported_plan_accepts_none_term_and_never_executes(tmp_path, monkeypatch):
    _, interpretation = _fixture(tmp_path)
    planned = _plan(DIVISION_GOAL, interpretation)
    assert planned["status"] == "unsupported"
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(
        _request(tmp_path, interpretation, goal=DIVISION_GOAL), planned["planId"], None
    )

    assert result["status"] == "unsupported"
    assert result["witness"] == WITNESS
    assert result["formalClaimRefuted"] is False
    assert result["spuriousnessEvidence"] is None
    assert result["realizationEvidence"] is None


@pytest.mark.parametrize(
    "unsafe", ["../outside.lean", "./Fixture/Lift.lean", "/etc/passwd", "Fixture//Lift.lean"]
)
def test_noncanonical_or_escaping_source_paths_reject_without_execution(
    tmp_path, monkeypatch, unsafe
):
    _, interpretation = _fixture(tmp_path)
    planned = _plan(GOAL, interpretation)
    interpretation["source"]["path"] = unsafe
    request = _request(tmp_path, interpretation)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_rejected(result)


def test_symlink_source_component_rejects_even_when_target_hash_matches(tmp_path, monkeypatch):
    real = tmp_path / "real"
    real.mkdir()
    target, interpretation = _fixture(real)
    linkroot = tmp_path / "linked"
    linkroot.mkdir()
    (linkroot / "Fixture").symlink_to(target.parent, target_is_directory=True)
    request = _request(linkroot, interpretation)
    planned = _plan(GOAL, interpretation)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    _assert_rejected(result)


def test_source_directory_is_not_accepted_as_regular_utf8_file(tmp_path, monkeypatch):
    source, interpretation = _fixture(tmp_path)
    source.unlink()
    source.mkdir()
    planned = _plan(GOAL, interpretation)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(
        _request(tmp_path, interpretation), planned["planId"], "by trivial"
    )

    _assert_rejected(result)


def test_correct_hash_does_not_make_invalid_utf8_source_acceptable(tmp_path, monkeypatch):
    invalid_utf8 = b"\xff\xfe"
    _, interpretation = _fixture(tmp_path, content=invalid_utf8)
    planned = _plan(GOAL, interpretation)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(
        _request(tmp_path, interpretation), planned["planId"], "by trivial"
    )

    _assert_rejected(result)


def test_expired_deadline_is_incomplete_before_process_and_request_is_unchanged(
    tmp_path, monkeypatch
):
    _, interpretation = _fixture(tmp_path)
    planned = _plan(GOAL, interpretation)
    request = _request(tmp_path, interpretation, deadlineMonotonic=time.monotonic() - 1)
    original = copy.deepcopy(request)
    _forbid_process(monkeypatch)

    result = check_nat_rational_lift(request, planned["planId"], "by trivial")

    assert result["status"] == "incomplete"
    assert result["witness"] == WITNESS
    assert result["originalClaimRefuted"] is False
    assert result["formalClaimRefuted"] is False
    assert result["spuriousnessEvidence"] is None
    assert result["realizationEvidence"] is None
    assert result["checkId"] is None
    assert request == original


def test_oversized_witness_is_rejected_without_echoing_unbounded_input(tmp_path, monkeypatch):
    _, interpretation = _fixture(tmp_path)
    request = _request(tmp_path, interpretation)
    planned = _plan(GOAL, interpretation)
    request["witness"]["id"] = "x" * (1024 * 1024 + 1)
    _forbid_process(monkeypatch)
    result = check_nat_rational_lift(request, planned["planId"], "by trivial")
    assert result["status"] == "rejected"
    assert result["witness"] is None
    assert result["formalClaimRefuted"] is False
    assert result["checkId"] is None
