"""Pure negative controls for public source-obligation workflow resource rules."""
from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any

import pytest
from support.proof_contract_obligation_planner import repeated_and_case, request_kwargs
from test_proof_contract_obligation_bundles import _request

from ladon.proof_contract_obligation_artifacts import obligations_artifact
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


@pytest.fixture
def api():
    return importlib.import_module("ladon.proof_contract_obligation_checks")


def _base_plan(kind: str):
    if kind == "two-leaves":
        _fixture, request = _request()
        return request
    case = repeated_and_case()
    return ContractObligationPlanRequest(**request_kwargs(case))


def _workflow_request(tmp_path: Path, plan_request: ContractObligationPlanRequest,
                      *, max_attempts: int = 8, terms: list[str] | None = None) -> dict[str, Any]:
    artifact = obligations_artifact(plan_request, analysis_id="analysis:pure-source-red")
    context_artifacts = [plan_request.derivation_artifact, *plan_request.contract_artifacts]
    result = artifact["payload"]["result"]
    providers_by_key = {}
    for route in result["routeComparisons"]:
        for row in route["backwardRequirements"]:
            ref = row.get("forwardContractRef")
            if not isinstance(ref, dict) or ref.get("kind") != "contract":
                continue
            key = (ref.get("artifactRef"), ref.get("kind"), ref.get("localId"))
            providers_by_key[key] = {"contractRef": ref,
                "providerSnapshot": {"selection": {"declaration": ref["localId"]}},
                "providerReadingId": "reading:provider:" + ref["localId"],
                "terms": list(terms if terms is not None else ["by synthetic candidate"])}
    return {"repoRoot": str(tmp_path), "analysisArtifact": artifact,
        "context": {"artifacts": context_artifacts},
        "sourceBindings": {"parentSnapshot": {"synthetic": "parent"},
            "parentReadingId": plan_request.desired_reading_identity["readingId"],
            "providers": list(providers_by_key.values())},
        "outputDir": str(tmp_path / "source-run"),
        "deadlineMonotonic": time.monotonic() + 60,
        "limits": {"timeout_seconds": 1, "max_output_bytes": 8 * 1024**2,
                   "max_rss_bytes": DEFAULT_MAX_RSS_BYTES},
        "maxCheckAttempts": max_attempts}


def _mock_native_validation(monkeypatch, analysis_artifact):
    from ladon import proof_contract_obligation_supervision as supervision

    calls = []

    def validate(artifact, context, **kwargs):
        calls.append((artifact, context, kwargs))
        return {"status": "completed", "result": analysis_artifact,
                "workerInputDigest": "sha256:" + "a" * 64, "bounds": {},
                "processReceipt": {"status": "completed"}}

    monkeypatch.setattr(supervision, "run_obligation_validation", validate)
    return calls


def _mock_candidate_constructor(monkeypatch, *, calls=None):
    from ladon import proof_contract_source_obligations as source

    calls = [] if calls is None else calls

    def construct(request):
        calls.append(request)
        return {"status": "candidate-goal", "capture": {"synthetic": "capture"},
                "selectedRequirement": {"contractRecord": {}}}

    monkeypatch.setattr(source, "instantiate_planned_source_leaf_requirement", construct)
    return calls


def _mock_completion(monkeypatch, outcome, calls=None):
    from ladon import proof_slice, source_goal_completion

    calls = [] if calls is None else calls
    monkeypatch.setattr(proof_slice, "pinned_toolchain", lambda _root: object())
    monkeypatch.setattr(source_goal_completion, "SourceGoalCompletionRequest",
                        lambda **kwargs: kwargs)

    def complete(request, *, runner):
        calls.append((request, runner))
        return outcome

    monkeypatch.setattr(source_goal_completion, "complete_source_goal", complete)
    return calls


def test_max_check_attempts_is_shared_across_distinct_source_demands(api, tmp_path, monkeypatch):
    plan_request = _base_plan("two-leaves")
    request = _workflow_request(tmp_path, plan_request, max_attempts=1)
    validation_calls = _mock_native_validation(monkeypatch, request["analysisArtifact"])
    constructors = _mock_candidate_constructor(monkeypatch)
    completions = _mock_completion(monkeypatch, {"status": "rejected", "replay": {"status": "rejected"}})

    result = api.check_obligation_sources(request)

    assert len(validation_calls) == 1
    assert len(result["sourceChecks"]) == 2
    assert len(constructors) == 2
    assert len(completions) == 1
    assert result["resourceAccounting"]["evidenceBytes"] > 0
    assert all(row["status"] == "unresolved" for row in result["sourceChecks"])
    assert result["wholeMethodAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"


@pytest.mark.parametrize("stop_stage", ["construction", "completion"])
def test_memory_stop_preserves_exact_report_back_and_prevents_later_work(
    api, tmp_path, monkeypatch, stop_stage,
):
    plan_request = _base_plan("two-leaves")
    request = _workflow_request(tmp_path, plan_request, max_attempts=8)
    _mock_native_validation(monkeypatch, request["analysisArtifact"])
    stop_message = memory_limit_message(DEFAULT_MAX_RSS_BYTES, DEFAULT_MAX_RSS_BYTES + 1)
    constructors = []
    completions = []

    if stop_stage == "construction":
        from ladon import proof_contract_source_obligations as source

        def construct(source_request):
            constructors.append(source_request)
            return {"status": "incomplete", "diagnostic": {
                "code": "resource-limit", "message": stop_message}}

        monkeypatch.setattr(source, "instantiate_planned_source_leaf_requirement", construct)
    else:
        _mock_candidate_constructor(monkeypatch, calls=constructors)
        _mock_completion(monkeypatch, {"status": "memory-limit", "diagnostic": {
            "message": stop_message}}, calls=completions)

    result = api.check_obligation_sources(request)

    assert result["status"] == "incomplete"
    assert result["memoryReportBackRequired"] is True
    assert len(constructors) == 1
    assert len(completions) == (0 if stop_stage == "construction" else 1)
    assert len(result["sourceChecks"]) == 2  # later demand is still visible as unresolved
    assert all(row["status"] == "unresolved" for row in result["sourceChecks"])
    assert all(row["sourceCheckStatus"] == "unresolved" for row in result["routes"])
    _assert_stop_authority_and_instruction(result, stop_message)


def test_repeated_incoming_occurrences_share_one_source_check(api, tmp_path, monkeypatch):
    plan_request = _base_plan("repeated")
    request = _workflow_request(tmp_path, plan_request, terms=[])
    _mock_native_validation(monkeypatch, request["analysisArtifact"])
    constructors = _mock_candidate_constructor(monkeypatch)
    completions = _mock_completion(monkeypatch, {"status": "completed"})

    result = api.check_obligation_sources(request)

    assert len(result["sourceChecks"]) == 1
    assert len(result["sourceChecks"][0]["incomingOccurrences"]) == 2
    assert len(constructors) == 1
    assert completions == []
    assert result["sourceChecks"][0]["status"] == "unresolved"
    assert result["wholeMethodAuthority"] == "none"


def _assert_stop_authority_and_instruction(result, stop_message):
    assert result["wholeMethodAuthority"] == "none"
    assert stop_message.startswith("Stop progress and report back to user:")
    assert result["stopReason"] == stop_message
