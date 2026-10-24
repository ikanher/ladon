"""Public-contract regressions for the staged proof-contract audit driver.

This suite describes the frozen #934 interface and deliberately runs no Lean commands. The propagation fixture is the repository's checked,
ordinary native fixture.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/proof_contract_propagation"
SCHEMA = "ladon-contract-audit-plan-v1"


def _driver():
    from ladon.proof_contract_audit import run_contract_audit
    return run_contract_audit


def _fixture_plan(*, stages=None):
    graph = json.loads((FIXTURE / "graph.json").read_text())
    context = json.loads((FIXTURE / "context.json").read_text())
    request = json.loads((FIXTURE / "request.json").read_text())
    contracts = [item for item in context["artifacts"]
                 if item.get("artifactKind") == "proofir.contract"]
    return {
        "schema": SCHEMA,
        "repoRoot": None,
        "sourceFiles": [],
        "limits": None,
        "stages": stages or [
            {"id": "propagate", "operation": "propagate", "request": {
                "graph": graph, "contracts": contracts, "request": request,
                "analysisId": "audit:fixture",
            }},
            {"id": "inspect", "operation": "inspect", "request": {
                "artifact": {"auditStage": "propagate", "pointer": ""},
                "context": context,
            }},
        ],
    }


def _write_plan(path: Path, plan):
    path.write_text(json.dumps(plan, sort_keys=True) + "\n")
    return path


def _read(path: Path):
    return json.loads(path.read_text())


def test_real_fixture_propagates_then_inspects_through_public_api(tmp_path):
    plan = _write_plan(tmp_path / "plan.json", _fixture_plan())
    report = _driver()(plan, tmp_path / "run")

    assert report["schema"] == "ladon-contract-audit-run-v1"
    assert report["status"] == "completed"
    assert [stage["id"] for stage in report["stages"]] == ["propagate", "inspect"]
    produced = _read(tmp_path / "run/stages/propagate.json")["result"]
    inspected = _read(tmp_path / "run/stages/inspect.json")["result"]
    assert produced["artifactKind"] == "proofir.contract-analysis"
    assert inspected["payload"]["result"]["complete"] is True


def test_partial_checkpoint_resumes_same_clock_and_keeps_prefix_bytes(tmp_path):
    plan = _write_plan(tmp_path / "plan.json", _fixture_plan())
    out = tmp_path / "run"
    first = _driver()(plan, out, max_stages=1)
    assert first["status"] == "partial"
    assert [stage["id"] for stage in first["stages"]] == ["propagate"]
    clock = copy.deepcopy(first["clock"])
    stage_path = out / "stages/propagate.json"
    original_stage = stage_path.read_bytes()
    original_run = (out / "run.json").read_bytes()

    resumed = _driver()(plan, tmp_path / "next", resume=out, max_stages=64)
    assert resumed["status"] == "completed"
    assert resumed["clock"] == clock
    assert stage_path.read_bytes() == original_stage
    assert (out / "run.json").read_bytes() == original_run
    assert [stage["id"] for stage in resumed["stages"]] == ["propagate", "inspect"]


def test_resume_rejects_modified_plan_result_and_runtime_without_launching(tmp_path, monkeypatch):
    run_contract_audit = _driver()
    plan_path = _write_plan(tmp_path / "plan.json", _fixture_plan())
    out = tmp_path / "run"
    run_contract_audit(plan_path, out, max_stages=1)
    calls = []

    def forbidden_runner(command, **kwargs):
        calls.append(command)
        raise AssertionError("resume drift validation must precede worker launch")

    plan = _read(plan_path)
    plan["stages"][0]["request"]["analysisId"] = "audit:changed"
    _write_plan(tmp_path / "changed-plan.json", plan)
    with pytest.raises((ValueError, OSError)):
        run_contract_audit(tmp_path / "changed-plan.json", tmp_path / "unused-plan",
                           resume=out, runner=forbidden_runner)

    original_stage = (out / "stages/propagate.json").read_bytes()
    # Result-envelope drift is checked before any continuation stage is launched.
    stage_path = out / "stages/propagate.json"
    envelope = _read(stage_path)
    envelope["result"]["payload"]["result"]["complete"] = False
    stage_path.write_text(json.dumps(envelope, sort_keys=True) + "\n")
    with pytest.raises((ValueError, OSError)):
        run_contract_audit(plan_path, tmp_path / "unused-result", resume=out,
                           runner=forbidden_runner)
    stage_path.write_bytes(original_stage)
    import ladon.proof_contract_audit as audit
    monkeypatch.setattr(audit, "_runtime_identity", lambda: "sha256:" + "0" * 64)
    with pytest.raises((ValueError, OSError)):
        run_contract_audit(plan_path, tmp_path / "unused-runtime", resume=out,
                           runner=forbidden_runner)
    assert calls == []


def test_refinement_is_reported_unavailable_after_preserving_completed_prefix(tmp_path):
    plan_obj = _fixture_plan(stages=[
        {"id": "first", "operation": "propagate", "request": {
            "graph": json.loads((FIXTURE / "graph.json").read_text()),
            "contracts": [x for x in json.loads((FIXTURE / "context.json").read_text())["artifacts"]
                          if x.get("artifactKind") == "proofir.contract"],
            "request": json.loads((FIXTURE / "request.json").read_text()),
            "analysisId": "audit:prefix",
        }},
        {"id": "future", "operation": "refine", "request": {"auditStage": "first", "pointer": ""}},
    ])
    report = _driver()(_write_plan(tmp_path / "plan.json", plan_obj), tmp_path / "run")

    assert report["status"] == "partial"
    assert report["stages"][0]["id"] == "first"
    assert report["code"] == "refinement-unavailable"
    assert _read(tmp_path / "run/stages/first.json")["result"]["artifactKind"] == "proofir.contract-analysis"


def test_memory_stop_reports_and_prevents_later_stage_or_resume(tmp_path):
    first_stage = _fixture_plan()["stages"][0]
    first_stage["id"] = "first"
    plan_obj = _fixture_plan(stages=[first_stage,
        {"id": "later", "operation": "refine", "request": {}},
    ])
    calls = []

    def memory_runner(command, **kwargs):
        calls.append((tuple(command), kwargs))
        from ladon.process_supervisor import ProcessResult
        return ProcessResult(tuple(command), -9, "", "synthetic memory stop", 0.01,
                             memory_limited=True)

    out = tmp_path / "run"
    report = _driver()(_write_plan(tmp_path / "plan.json", plan_obj), out,
                       runner=memory_runner)
    assert report["status"] == "stopped"
    assert report["code"] == "memory-limit"
    assert "Stop" in report["message"]
    assert [stage["id"] for stage in report["stages"]] == ["first"]
    assert len(calls) == 1

    calls.clear()
    with pytest.raises((ValueError, OSError)):
        _driver()(tmp_path / "plan.json", tmp_path / "resume", resume=out,
                  runner=memory_runner)
    assert calls == []


def test_bad_reference_unknown_operation_and_bad_limits_are_rejected_before_output(tmp_path):
    base = _fixture_plan(stages=[
        {"id": "one", "operation": "inspect", "request": {
            "artifact": {"auditStage": "missing", "pointer": ""}, "context": []}},
    ])
    out = tmp_path / "bad-ref"
    with pytest.raises((ValueError, TypeError)):
        _driver()(_write_plan(tmp_path / "bad-ref.json", base), out)
    assert not out.exists()

    for key, value in (("operation", "unknown-op"),):
        invalid = _fixture_plan(stages=[{"id": "one", key: value, "request": {}}])
        with pytest.raises((ValueError, TypeError)):
            _driver()(_write_plan(tmp_path / "bad-op.json", invalid), tmp_path / "bad-op")

    invalid = _fixture_plan()
    invalid["limits"] = {"timeout_seconds": float("inf"), "max_rss_bytes": 1,
                         "max_output_bytes": 8 * 1024 * 1024}
    with pytest.raises((ValueError, TypeError)):
        _driver()(_write_plan(tmp_path / "bad-limits.json", invalid), tmp_path / "bad-limits")

    invalid = _fixture_plan()
    invalid["repoRoot"] = str(Path(__file__).resolve().parents[1])
    invalid["sourceFiles"] = ["../outside.md"]
    with pytest.raises((ValueError, TypeError, OSError)):
        _driver()(_write_plan(tmp_path / "bad-path.json", invalid), tmp_path / "bad-path")
    assert not (tmp_path / "bad-path").exists()


def test_contract_cli_exposes_the_audit_command():
    from ladon.proof_contract_cli import contract_main

    with pytest.raises(SystemExit) as result:
        contract_main(["audit", "--help"])
    assert result.value.code == 0
