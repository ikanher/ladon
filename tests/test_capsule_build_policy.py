"""Public contract for bounded capsule build scheduling."""
from __future__ import annotations

import json
import time
from itertools import pairwise
from types import SimpleNamespace

import pytest

from ladon.theorem_capsule_models import CapsuleInvocationError
from ladon.theorem_capsule_replay import replay_theorem_capsule
from ladon.theorem_cli import theorem_main


def test_service_rejects_unknown_build_policy_before_replay(monkeypatch, tmp_path):
    called = False

    def replay(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("ladon.theorem_capsule_replay._replay_validated", replay)
    with pytest.raises(CapsuleInvocationError, match="build policy"):
        replay_theorem_capsule(tmp_path / "capsule", build_policy="pretend-bounded")
    assert called is False


def test_replay_cli_forwards_ordered_policy(monkeypatch, capsys, tmp_path):
    forwarded = []
    monkeypatch.setattr(
        "ladon.theorem_capsule_replay.replay_theorem_capsule",
        lambda *args, **kwargs: forwarded.append(kwargs) or {
            "status": "verified", "receiptIdentity": "sha256:test", "stages": []
        },
    )
    assert theorem_main([
        "replay", str(tmp_path), "--build-policy", "ordered", "--format", "json"
    ]) == 0
    json.loads(capsys.readouterr().out)
    assert forwarded[0]["build_policy"] == "ordered"


def test_extract_verify_cli_forwards_ordered_policy(monkeypatch, capsys, tmp_path):
    plan = SimpleNamespace(identity="sha256:plan")
    manifest = SimpleNamespace(identity="sha256:capsule", payload={"status": "materialized_unverified"})
    monkeypatch.setattr("ladon.theorem_cli.plan_theorem_capsule", lambda *_args, **_kwargs: plan)
    monkeypatch.setattr("ladon.theorem_capsule_materialization.materialize_theorem_capsule", lambda *_args, **_kwargs: manifest)
    forwarded = []
    monkeypatch.setattr(
        "ladon.theorem_capsule_replay.replay_theorem_capsule",
        lambda *args, **kwargs: forwarded.append(kwargs) or {
            "status": "verified", "receiptIdentity": "sha256:test", "stages": []
        },
    )
    assert theorem_main([
        "extract", "Fixture.chosen", "--repo-root", str(tmp_path),
        "--output", str(tmp_path / "capsule"), "--verify",
        "--build-policy", "ordered", "--format", "json",
    ]) == 0
    json.loads(capsys.readouterr().out)
    assert forwarded[0]["build_policy"] == "ordered"


def _plan(modules, edges):
    return SimpleNamespace(target={"module": modules[0]}, payload={"buildGraph": {
        "modules": [{"module": module, "path": f"{module}.lean"} for module in modules],
        "edges": edges,
    }})


def test_ordered_modules_topologically_places_dependencies_first():
    from ladon.theorem_capsule_build import ordered_modules

    plan = _plan(
        ["A", "B", "C"],
        [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}],
    )
    assert ordered_modules(plan) == ["C", "B", "A"]


@pytest.mark.parametrize("modules,edges", [
    (["A", "B"], [{"source": "A", "target": "Missing"}]),
    (["A", "B"], [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}]),
    (["A", "A"], []),
])
def test_ordered_modules_fails_closed_for_malformed_or_cyclic_graph(modules, edges):
    from ladon.theorem_capsule_build import ordered_modules

    with pytest.raises((CapsuleInvocationError, ValueError)):
        ordered_modules(_plan(modules, edges))


def test_ordered_build_uses_two_steps_per_module_and_one_decreasing_deadline(monkeypatch, tmp_path):
    from ladon.theorem_capsule_build import run_ordered_build

    plan = _plan(
        ["A", "B", "C"],
        [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}],
    )
    calls = []

    class Result:
        timed_out = output_limited = memory_limited = False
        returncode = 0
        stdout = stderr = ""
        peak_rss_bytes = 10

    def run_stage(command, cwd, timeout_seconds, max_rss_bytes, environment, **kwargs):
        calls.append((command, timeout_seconds, kwargs["stage"]))
        time.sleep(0.005)
        return {"status": None, "result": Result(), "row": {"returncode": 0}}

    result = run_ordered_build(plan, tmp_path, 30.0, 1000, {}, run_stage)
    assert result["status"] is None
    assert [row[0] for row in calls] == [
        ["lake", "--no-build", "build", "+C:deps"],
        ["lake", "build", "+C:leanArts"],
        ["lake", "--no-build", "build", "+B:deps"],
        ["lake", "build", "+B:leanArts"],
        ["lake", "--no-build", "build", "+A:deps"],
        ["lake", "build", "+A:leanArts"],
    ]
    budgets = [row[1] for row in calls]
    assert budgets[0] <= 30.0
    assert all(left > right > 0 for left, right in pairwise(budgets))
    assert result["row"]["stage"] == "lean_build"
    assert len(result["row"]["steps"]) == len(calls)


def test_ordered_build_stops_on_memory_failure(monkeypatch, tmp_path):
    from ladon.process_supervisor import ProcessResult
    from ladon.theorem_capsule_build import run_ordered_build

    plan = _plan(["A", "B", "C"], [])
    calls = []
    memory_result = ProcessResult(
        command=("lake", "build"), returncode=-15, stdout="", stderr="",
        elapsed_seconds=0.01, timed_out=False, output_limited=False,
        memory_limited=True, peak_rss_bytes=1001,
    )

    def run_stage(command, cwd, timeout_seconds, max_rss_bytes, environment, **kwargs):
        calls.append(command)
        return {"status": "resource-limit", "result": memory_result,
                "row": {"stage": kwargs["stage"], "memoryLimited": True}}

    result = run_ordered_build(plan, tmp_path, 30.0, 1000, {}, run_stage)
    assert result["status"] == "resource-limit"
    assert len(calls) == 1
    assert result["row"]["steps"][0]["memoryLimited"] is True


def test_replay_receipt_records_requested_and_effective_policy(monkeypatch, tmp_path):
    expected = {"status": "resource-limit", "stages": [{"stage": "lean_build"}]}
    monkeypatch.setattr("ladon.theorem_capsule_replay._replay_validated", lambda *_args: expected)
    receipt = replay_theorem_capsule(tmp_path, build_policy="ordered")
    assert receipt["buildPolicy"]["requested"] == "ordered"
    assert receipt["buildPolicy"]["effective"] == "ordered"
