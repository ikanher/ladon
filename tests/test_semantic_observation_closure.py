from __future__ import annotations

import copy
import hashlib
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from support.semantic_evidence import check_ref, digest, semantic_evidence

from ladon.evidence_receipt import build_evidence_receipt
from ladon.proofir_v3 import canonical_bytes, detached_content_id, validate_envelope_batch
from ladon.semantic_candidate_batch_worker import _materialize_partial_row
from ladon.semantic_candidate_worker import SemanticCandidateRequest
from ladon.semantic_result_projection import SemanticProjectionError, project_semantic_result


def _check(
    label: str,
    *,
    candidate: str | None = None,
    status: str = "accepted",
    local_context: tuple[dict[str, str], ...] = (),
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    candidate = candidate or f"Main.{label}"
    artifacts, registry, receipt = semantic_evidence(
        label,
        candidate=candidate,
        status=status,
        local_context=local_context,
    )
    check = {
        "status": status,
        "applicationTerm": candidate if status != "rejected" else None,
        "substitutions": [],
        "residualPremises": (
            [{"typeDisplay": "True", "typeStructural": "True"}]
            if status == "applicable-with-residuals"
            else []
        ),
        "dischargedHypotheses": [],
        "failureStage": "candidate-not-found" if status == "rejected" else None,
        "environmentRef": artifacts[0]["environmentRef"],
        "checkRunId": artifacts[1]["payload"]["checkRunId"],
        "checkRunRef": {
            "artifactRef": artifacts[1]["artifactId"],
            "kind": "check-run",
            "localId": artifacts[1]["payload"]["checkRunId"],
        },
        "evidenceReceipt": receipt,
        "artifacts": artifacts,
    }
    return check, registry


def _direct(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        **check,
    }


def _discovery(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [str(row.get("check", {}).get("status")) for row in rows]
    completed = sum(
        status in {"accepted", "applicable-with-residuals", "rejected"}
        for status in statuses
    )
    status = (
        "unavailable"
        if not rows
        else (
            "available"
            if completed == len(rows)
            else (
                "partial"
                if completed or "provisional-observation" in statuses
                else "failed"
            )
        )
    )
    return {
        "schema": "ladon-verified-discovery-result-v1",
        "operation": "discover",
        "status": status,
        "request": {
            "module": "Main",
            "goal": "True",
            "localContext": [],
            "maxCandidates": max(1, len(rows)),
        },
        "candidates": rows,
        "coverage": {"shortlisted": len(rows), "truncated": False},
        "shortlist": {},
        "ranking": {},
        "nonclaims": [],
    }


def _mutate_check_artifact(
    check: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    artifact = copy.deepcopy(check["artifacts"][1])
    mutate(artifact)
    artifact["artifactId"] = detached_content_id(artifact)
    check["artifacts"][1] = artifact
    if isinstance(check.get("checkRunRef"), dict):
        check["checkRunRef"]["artifactRef"] = artifact["artifactId"]
    registry.clear()
    registry.update({row["artifactId"]: row for row in check["artifacts"]})
    validate_envelope_batch(check["artifacts"])


def test_direct_projector_rejects_status_check_artifact_contradiction() -> None:
    check, registry = _check("status")

    def reject_application(artifact: dict[str, Any]) -> None:
        artifact["payload"]["results"][0]["result"] = "rejected"

    _mutate_check_artifact(check, registry, reject_application)
    with pytest.raises(SemanticProjectionError, match="contradictory terminal results"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)


def test_direct_projector_rejects_authority_and_completeness_contradictions() -> None:
    check, registry = _check("authority")

    def change_authority(artifact: dict[str, Any]) -> None:
        artifact["payload"]["guarantee"]["authorityBasis"] = "kernel-check"

    _mutate_check_artifact(check, registry, change_authority)
    with pytest.raises(SemanticProjectionError, match="authority disagrees"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)

    check, registry = _check("complete")
    receipt = _replacement_receipt(check, outcome="accepted", completeness="partial")
    _replace_bound_receipt(check, registry, receipt)
    with pytest.raises(SemanticProjectionError, match="completeness contradicts"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)


def test_direct_projector_rejects_receipt_outcome_and_local_context_contradictions() -> None:
    check, registry = _check("outcome")
    receipt = _replacement_receipt(check, outcome="rejected", completeness="complete")
    _replace_bound_receipt(check, registry, receipt)
    with pytest.raises(SemanticProjectionError, match="status disagrees"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)

    check, registry = _check(
        "context", local_context=({"name": "h", "type": "Bool"},)
    )
    check["callerLocalContext"] = [{"name": "h", "type": "Nat"}]
    with pytest.raises(SemanticProjectionError, match="requested prefix"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)


@pytest.mark.parametrize(("field", "value"), [("goal", "False"), ("module", "Foreign")])
def test_candidate_goal_subject_closes_receipt_module_and_goal(
    field: str, value: str
) -> None:
    check, registry = _check(f"subject-{field}")
    original = check["evidenceReceipt"]
    subject = {**original["subject"], field: value}
    receipt = build_evidence_receipt(
        subject=subject,
        execution_binding=original["executionBinding"],
        observation_state=original["observationState"],
        operation_outcome=original["operationOutcome"],
        authority_basis=original["authorityBasis"],
        analysis_completeness=original["analysisCompleteness"],
        source_freshness=original["sourceFreshness"],
        environment_match=original["environmentMatch"],
        environment_ref=original["environmentRef"],
        check_run_ref=original["checkRunRef"],
        limitations=original["limitations"],
    )
    _replace_bound_receipt(check, registry, receipt)

    with pytest.raises(SemanticProjectionError, match="goal subject disagrees"):
        project_semantic_result(
            _direct(check), projection="llm", registered_artifacts=registry
        )


def test_check_operation_class_is_closed() -> None:
    check, registry = _check("operation")

    def replace_operation(artifact: dict[str, Any]) -> None:
        artifact["payload"]["operation"] = "unrelated-observation"

    _mutate_check_artifact(check, registry, replace_operation)
    with pytest.raises(SemanticProjectionError, match="different check operation"):
        project_semantic_result(
            _direct(check), projection="llm", registered_artifacts=registry
        )


def test_weak_failure_receipt_is_bound_to_candidate_and_request() -> None:
    receipt = build_evidence_receipt(
        subject={
            "module": "Main",
            "candidate": "Main.foreign",
            "goal": "True",
            "localContext": [],
        },
        execution_binding="ambient-observed",
        observation_state="failed",
        operation_outcome="failed",
        authority_basis="not-assessed",
        analysis_completeness="not-assessed",
        source_freshness="unknown",
        environment_match="unknown",
    )
    payload = {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        "status": "failed-checker",
        "candidate": "Main.expected",
        "evidenceReceipt": receipt,
        "artifacts": [],
    }

    with pytest.raises(SemanticProjectionError, match="weak observation subject"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts={}
        )

def test_discovery_rejects_cross_environment_check_pairing() -> None:
    check, registry = _check("environment")
    environment_a = check["artifacts"][0]
    environment_b = copy.deepcopy(environment_a)
    environment_b["payload"]["compiledModules"][0]["digest"] = digest("foreign-olean")
    environment_b["environmentRef"] = "sha256:" + hashlib.sha256(
        canonical_bytes(environment_b["payload"])
    ).hexdigest()
    environment_b["artifactId"] = detached_content_id(environment_b)
    check_artifact = copy.deepcopy(check["artifacts"][1])
    check_artifact["environmentRef"] = environment_b["environmentRef"]
    check_artifact["payload"]["inputs"]["environmentRef"] = environment_b["environmentRef"]
    check_artifact["payload"]["inputs"]["artifactRefs"] = [environment_b["artifactId"]]
    check_artifact["artifactId"] = detached_content_id(check_artifact)
    validate_envelope_batch([environment_b, check_artifact])
    check["artifacts"] = [environment_a, environment_b, check_artifact]
    check["checkRunRef"]["artifactRef"] = check_artifact["artifactId"]
    registry = {row["artifactId"]: row for row in check["artifacts"]}

    with pytest.raises(SemanticProjectionError, match="environment identities"):
        project_semantic_result(
            _discovery([{"name": "Main.environment", "check": check}]),
            projection="llm",
            registered_artifacts=registry,
        )


def test_omitted_candidate_must_resolve_before_population_accounting() -> None:
    rows: list[dict[str, Any]] = []
    registry: dict[str, dict[str, Any]] = {}
    for index in range(8):
        candidate = f"Main.valid{index}"
        check, row_registry = _check(f"valid-{index}", candidate=candidate)
        registry.update(row_registry)
        rows.append({"name": candidate, "check": check})
    dangling, _unused = _check("dangling", candidate="Main.dangling")
    dangling["artifacts"] = []
    rows.append({"name": "Main.dangling", "check": dangling})

    with pytest.raises(SemanticProjectionError, match="unresolved or not registered"):
        project_semantic_result(
            _discovery(rows), projection="llm", registered_artifacts=registry
        )


def test_discovery_rejects_duplicate_canonical_candidate_names() -> None:
    check, registry = _check("duplicate", candidate="Main.same")
    rows = [
        {"name": "Main.same", "check": copy.deepcopy(check)},
        {"name": "Main.same", "check": copy.deepcopy(check)},
    ]

    with pytest.raises(SemanticProjectionError, match="candidate names must be unique"):
        project_semantic_result(
            _discovery(rows), projection="llm", registered_artifacts=registry
        )


@pytest.mark.parametrize(
    ("owner", "field"),
    [("request", "maxCandidates"), ("coverage", "shortlisted"), ("coverage", "truncated")],
)
def test_discovery_requires_canonical_population_bounds(owner: str, field: str) -> None:
    check, registry = _check(f"missing-{field}")
    payload = _discovery([{"name": f"Main.missing-{field}", "check": check}])
    del payload[owner][field]

    with pytest.raises(SemanticProjectionError, match="requires maxCandidates"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts=registry
        )


def test_omitted_candidate_scratch_must_resolve_before_card_selection() -> None:
    rows: list[dict[str, Any]] = []
    registry: dict[str, dict[str, Any]] = {}
    for index in range(8):
        candidate = f"Main.visible{index}"
        check, row_registry = _check(f"visible-{index}", candidate=candidate)
        registry.update(row_registry)
        rows.append({"name": candidate, "check": check})
    candidate = "Main.hidden-scratch"
    parent, parent_registry = _check("hidden-parent", candidate=candidate)
    scratch_artifacts, _scratch_registry, scratch_receipt = semantic_evidence(
        "hidden-scratch", candidate=candidate, status="compiled", scratch=True
    )
    parent["scratch"] = {
        "status": "compiled",
        "applicationTerm": candidate,
        "sourceDigest": digest("scratch-source:hidden-scratch"),
        "environmentRef": scratch_artifacts[0]["environmentRef"],
        "checkRunRef": {
            "artifactRef": scratch_artifacts[1]["artifactId"],
            "kind": "check-run",
            "localId": check_ref("hidden-scratch"),
        },
        "parentCheckRunRef": parent["checkRunId"],
        "evidenceReceipt": scratch_receipt,
        "artifacts": [],
    }
    registry.update(parent_registry)
    rows.append({"name": candidate, "check": parent})

    with pytest.raises(SemanticProjectionError, match="unresolved or not registered"):
        project_semantic_result(
            _discovery(rows), projection="llm", registered_artifacts=registry
        )


def test_result_subject_failure_stage_and_application_shape_are_closed() -> None:
    rejected, registry = _check("rejected", status="rejected")
    rejected["failureStage"] = "application-rejected"
    with pytest.raises(SemanticProjectionError, match="failure stage disagrees"):
        project_semantic_result(
            _direct(rejected), projection="llm", registered_artifacts=registry
        )

    check, registry = _check("subject")

    def move_result_to_statement(artifact: dict[str, Any]) -> None:
        statement = next(
            row for row in artifact["subjectRefs"] if row["kind"] == "statement"
        )
        artifact["payload"]["results"] = [
            {
                "subjectRef": {"kind": "statement", "localId": statement["localId"]},
                "result": "accepted",
                "diagnostics": [],
            }
        ]

    _mutate_check_artifact(check, registry, move_result_to_statement)
    with pytest.raises(SemanticProjectionError, match="expected subject kind"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)

    check, registry = _check("shape")

    check["applicationTerm"] = "Main.other"
    with pytest.raises(SemanticProjectionError, match="applicationTerm disagrees"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)


def test_goal_and_rejected_declaration_results_use_their_exact_owned_subjects() -> None:
    accepted, registry = _check("goal-result")

    def move_goal_result(artifact: dict[str, Any]) -> None:
        foreign = {
            "kind": "statement",
            "localId": "statement:foreign",
            "display": "False",
        }
        artifact["subjectRefs"].append(foreign)
        artifact["payload"]["inputs"]["subjectRefs"].append(
            {"kind": "statement", "localId": "statement:foreign"}
        )
        result = next(
            row
            for row in artifact["payload"]["results"]
            if row["subjectRef"]["kind"] == "statement"
        )
        result["subjectRef"] = {"kind": "statement", "localId": "statement:foreign"}

    _mutate_check_artifact(accepted, registry, move_goal_result)
    with pytest.raises(SemanticProjectionError, match="bound to its goal"):
        project_semantic_result(
            _direct(accepted), projection="llm", registered_artifacts=registry
        )

    rejected, registry = _check("declaration-result", status="rejected")

    def move_rejection(artifact: dict[str, Any]) -> None:
        foreign = {
            "kind": "declaration",
            "localId": "declaration:foreign",
            "display": "Main.foreign",
        }
        artifact["subjectRefs"].append(foreign)
        artifact["payload"]["inputs"]["subjectRefs"].append(
            {"kind": "declaration", "localId": "declaration:foreign"}
        )
        artifact["payload"]["results"][0]["subjectRef"] = {
            "kind": "declaration",
            "localId": "declaration:foreign",
        }

    _mutate_check_artifact(rejected, registry, move_rejection)
    with pytest.raises(SemanticProjectionError, match="different declaration"):
        project_semantic_result(
            _direct(rejected), projection="llm", registered_artifacts=registry
        )


def test_failure_diagnostics_cannot_be_borrowed_from_an_unrelated_result() -> None:
    rejected, registry = _check("diagnostic-owner", status="rejected")

    def move_diagnostic(artifact: dict[str, Any]) -> None:
        diagnostic = artifact["payload"]["results"][0]["diagnostics"].pop()
        statement = next(
            row for row in artifact["subjectRefs"] if row["kind"] == "statement"
        )
        artifact["payload"]["results"].append(
            {
                "subjectRef": {"kind": "statement", "localId": statement["localId"]},
                "result": "rejected",
                "diagnostics": [diagnostic],
            }
        )

    _mutate_check_artifact(rejected, registry, move_diagnostic)
    with pytest.raises(SemanticProjectionError, match="failure stage disagrees"):
        project_semantic_result(
            _direct(rejected), projection="llm", registered_artifacts=registry
        )


def test_candidate_and_scratch_status_vocabularies_are_closed() -> None:
    with pytest.raises(SemanticProjectionError, match="unsupported semantic candidate status"):
        project_semantic_result(
            _direct({"status": "accepted-" + "x" * 50_000}),
            projection="llm",
            registered_artifacts={},
        )

    check, registry = _check("scratch-parent")
    check["scratch"] = {"status": "compiled-" + "x" * 50_000}
    with pytest.raises(SemanticProjectionError, match="unsupported semantic scratch status"):
        project_semantic_result(_direct(check), projection="llm", registered_artifacts=registry)


def test_provisional_prefix_remains_process_observation_with_partial_completeness() -> None:
    artifacts, registry, receipt = semantic_evidence(
        "prefix",
        candidate="Main.prefix",
        authority_basis="process-observation",
        completeness="partial",
    )
    check_artifact = artifacts[1]
    check_artifact["payload"]["results"][0]["diagnostics"] = [
        {
            "stage": "batch-process",
            "code": "timeout",
            "pointer": "/process",
            "message": "partial batch",
            "order": 0,
        }
    ]
    application = next(
        row
        for row in check_artifact["subjectRefs"]
        if row["kind"] == "candidate-application"
    )
    application["searchShape"]["processOutcome"] = "timeout"
    check_artifact["artifactId"] = detached_content_id(check_artifact)
    validate_envelope_batch(artifacts)
    registry = {row["artifactId"]: row for row in artifacts}
    check = {
        "status": "provisional-observation",
        "observedStatus": "accepted",
        "batchTerminal": False,
        "processOutcome": "timeout",
        "applicationTerm": "Main.prefix",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "environmentRef": artifacts[0]["environmentRef"],
        "checkRunRef": check_ref("prefix"),
        "evidenceReceipt": receipt,
        "artifacts": artifacts,
    }

    projected = project_semantic_result(
        _discovery([{"name": "Main.prefix", "check": check}]),
        projection="llm",
        registered_artifacts=registry,
    )

    projected_check = projected["candidates"][0]["check"]
    assert projected_check["status"] == "provisional-observation"
    assert projected_check["authority"]["authorityBasis"] == "process-observation"
    assert projected_check["authority"]["analysisCompleteness"] == "partial"


def test_real_partial_rejected_batch_artifact_projects_with_exact_application_owner(
    tmp_path: Path,
) -> None:
    from support.proofir_v3_native import environment_artifact

    request = SemanticCandidateRequest(
        Path("/repo"),
        "Main",
        "True",
        "Main.rejected",
        local_context=({"name": "h", "type": "True"},),
    )
    environment = environment_artifact()
    observed_context = [
        {
            "localId": "local:0",
            "userName": "h",
            "binderInfo": "default",
            "typeDisplay": "True",
            "typeStructural": "Lean.Expr.const `True []",
            "valueStructural": None,
            "dependencies": [],
            "origin": "caller",
        }
    ]
    row = {
        "candidate": "Main.rejected",
        "status": "rejected",
        "applicationTerm": None,
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "failureStage": "candidate-not-found",
        "diagnostic": "unknown declaration",
    }
    helper = tmp_path / "SemanticBatch.lean"
    helper.write_text("-- fixture\n")
    process = SimpleNamespace(
        command=("lean",),
        returncode=-1,
        stdout="",
        stderr="timeout",
        timed_out=True,
        output_limited=False,
        memory_limited=False,
    )
    partial = _materialize_partial_row(
        request,
        helper,
        process,
        observed_context,
        environment,
        row,
    )
    check = {
        **partial,
        "status": "provisional-observation",
        "observedStatus": "rejected",
    }
    artifacts = check["artifacts"]
    registry = {artifact["artifactId"]: artifact for artifact in artifacts}

    projected = project_semantic_result(
        _discovery([{"name": request.candidate, "check": check}]),
        projection="llm",
        registered_artifacts=registry,
    )

    assert projected["candidates"][0]["check"]["status"] == "provisional-observation"


def test_discovery_availability_and_coverage_are_derived_from_full_population() -> None:
    row = {"name": "Main.unassessed", "check": {"status": "unassessed"}}
    payload = _discovery([row])
    payload["status"] = "available"
    payload["coverage"] = {"accepted": 99}

    with pytest.raises(SemanticProjectionError, match="availability disagrees"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts={}
        )

    payload["status"] = "failed"
    with pytest.raises(SemanticProjectionError, match="coverage accepted disagrees"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts={}
        )

    payload["coverage"] = {"shortlisted": 1, "truncated": False}
    projected = project_semantic_result(
        payload, projection="llm", registered_artifacts={}
    )
    assert projected["coverage"]["canonical"] == {
        "submitted": 1,
        "completed": 0,
        "accepted": 0,
        "rejected": 0,
        "unassessed": 1,
        "failed": 0,
        "timeouts": 0,
        "outputLimited": 0,
        "memoryLimited": 0,
        "invalidWorkerOutput": 0,
        "scratchAttempted": 0,
        "scratchCompiled": 0,
        "shortlisted": 1,
        "truncated": False,
    }


def test_compact_projection_rejects_wrong_schema_and_producer_identities() -> None:
    with pytest.raises(SemanticProjectionError, match="mismatched result schema"):
        project_semantic_result(
            {
                "schema": "foreign-v1",
                "operation": "check-candidate",
                "status": "unassessed",
            },
            projection="llm",
            registered_artifacts={},
        )

    check, registry = _check("identity")
    payload = _discovery([{"name": "Main.identity", "check": check}])
    payload["requestIdentity"] = digest("wrong-request")
    with pytest.raises(SemanticProjectionError, match="request identity disagrees"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts=registry
        )

    payload.pop("requestIdentity")
    payload["resultIdentity"] = digest("wrong-result")
    with pytest.raises(SemanticProjectionError, match="result identity disagrees"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts=registry
        )


def _replacement_receipt(
    check: dict[str, Any], *, outcome: str, completeness: str
) -> dict[str, Any]:
    receipt = check["evidenceReceipt"]
    return build_evidence_receipt(
        subject=receipt["subject"],
        execution_binding=receipt["executionBinding"],
        observation_state="live",
        operation_outcome=outcome,
        authority_basis=receipt["authorityBasis"],
        analysis_completeness=completeness,
        source_freshness=receipt["sourceFreshness"],
        environment_match=receipt["environmentMatch"],
        environment_ref=receipt["environmentRef"],
        check_run_ref=receipt["checkRunRef"],
        limitations=receipt["limitations"],
    )


def _replace_bound_receipt(
    check: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    receipt: dict[str, Any],
) -> None:
    check["evidenceReceipt"] = receipt

    def replace(artifact: dict[str, Any]) -> None:
        artifact["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"] = receipt

    _mutate_check_artifact(check, registry, replace)


def test_scratch_failure_requires_attributable_failure_stage() -> None:
    parent, registry = _check("parent")
    artifacts, scratch_registry, receipt = semantic_evidence(
        "scratch-timeout",
        candidate="Main.parent",
        status="timeout",
        scratch=True,
    )
    scratch = {
        "status": "timeout",
        "applicationTerm": "Main.parent",
        "sourceDigest": digest("scratch-source:scratch-timeout"),
        "environmentRef": artifacts[0]["environmentRef"],
        "checkRunRef": check_ref("scratch-timeout"),
        "parentCheckRunRef": parent["checkRunId"],
        "evidenceReceipt": receipt,
        "artifacts": artifacts,
    }
    parent["scratch"] = scratch
    registry.update(scratch_registry)

    def obscure_failure(artifact: dict[str, Any]) -> None:
        artifact["payload"]["results"][0]["diagnostics"][0]["stage"] = "foreign"

    _mutate_check_artifact(scratch, registry, obscure_failure)
    registry.update({row["artifactId"]: row for row in parent["artifacts"]})
    with pytest.raises(SemanticProjectionError, match="status disagrees"):
        project_semantic_result(_direct(parent), projection="llm", registered_artifacts=registry)


@pytest.mark.parametrize(
    "swapped_status", ["output-limited", "memory-limited", "process-failed"]
)
def test_scratch_failure_status_is_bound_to_its_exact_diagnostic(
    swapped_status: str,
) -> None:
    parent, registry = _check("scratch-status-parent")
    artifacts, scratch_registry, receipt = semantic_evidence(
        "scratch-status",
        candidate="Main.scratch-status-parent",
        status="timeout",
        scratch=True,
    )
    parent["scratch"] = {
        "status": swapped_status,
        "applicationTerm": "Main.scratch-status-parent",
        "sourceDigest": digest("scratch-source:scratch-status"),
        "environmentRef": artifacts[0]["environmentRef"],
        "checkRunRef": check_ref("scratch-status"),
        "parentCheckRunRef": parent["checkRunId"],
        "evidenceReceipt": receipt,
        "artifacts": artifacts,
    }
    registry.update(scratch_registry)

    with pytest.raises(SemanticProjectionError, match="status disagrees"):
        project_semantic_result(
            _direct(parent), projection="llm", registered_artifacts=registry
        )
