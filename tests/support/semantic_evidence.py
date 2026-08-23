"""Canonical semantic evidence fixtures shared by compact-transport tests."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.evidence_receipt import build_evidence_receipt
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
from support.proofir_v3_native import envelope, environment_artifact


def digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def check_ref(label: str) -> str:
    return "check:" + hashlib.sha256(label.encode()).hexdigest()


def semantic_evidence(
    label: str = "main",
    *,
    candidate: str | None = None,
    goal: str = "True",
    status: str = "accepted",
    authority_basis: str = "elaborator-check",
    completeness: str | None = None,
    failure_stage: str = "candidate-not-found",
    scratch: bool = False,
    local_context: Sequence[dict[str, str]] = (),
    application_term: str | None = None,
    substitutions: Sequence[Mapping[str, Any]] = (),
    residual_premises: Sequence[Mapping[str, Any]] | None = None,
    discharged_hypotheses: Sequence[Mapping[str, Any]] = (),
    source_digest: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    """Return one valid environment/check pair, full resolver, and bound receipt."""

    candidate = candidate or f"Main.{label}"
    environment = environment_artifact()
    check_run_id = check_ref(label)
    receipt = semantic_receipt(
        label,
        candidate=candidate,
        goal=goal,
        status=status,
        authority_basis=authority_basis,
        completeness=completeness,
        scratch=scratch,
        local_context=local_context,
    )
    authority_basis = str(receipt["authorityBasis"])
    application_term = application_term or candidate
    residuals = _fixture_residuals(status, residual_premises)
    input_subjects, results, subjects, operation = _semantic_check_layout(
        label,
        candidate,
        goal,
        status,
        failure_stage,
        scratch,
        check_run_id,
        application_term,
        substitutions,
        residuals,
        discharged_hypotheses,
        local_context,
        source_digest or digest(f"scratch-source:{label}"),
    )
    check = envelope(
        "proofir.check-run",
        {
            "checkRunId": check_run_id,
            "checker": {
                "name": "Lean",
                "version": "4.fixture",
                "implementationDigest": digest("helper"),
                "executableDigest": digest("lean"),
            },
            "operation": operation,
            "inputs": {
                "environmentRef": environment["environmentRef"],
                "subjectRefs": [_compact(subject) for subject in input_subjects],
                "artifactRefs": [environment["artifactId"]],
            },
            "results": results,
            "outputs": {"stdoutDigest": digest("stdout"), "stderrDigest": digest("stderr")},
            "bounds": {"timeoutMs": 1_000, "maxOutputBytes": 1_048_576},
            "guarantee": {
                "scope": "process-exit" if authority_basis == "process-observation" else "route",
                "statement": "fixture semantic observation",
                "authorityBasis": authority_basis,
            },
        },
        subjects,
        environment=environment["environmentRef"],
    )
    check["extensions"] = {
        "ladon.process-observation/v1": {"evidenceReceipt": receipt}
    }
    check["artifactId"] = detached_content_id(check)
    validate_envelope_batch([environment, check])
    artifacts = [environment, check]
    return artifacts, {row["artifactId"]: row for row in artifacts}, receipt


def _semantic_check_layout(
    label: str,
    candidate: str,
    goal: str,
    status: str,
    failure_stage: str,
    scratch: bool,
    check_run_id: str,
    application_term: str,
    substitutions: Sequence[Mapping[str, Any]],
    residual_premises: Sequence[Mapping[str, Any]],
    discharged_hypotheses: Sequence[Mapping[str, Any]],
    local_context: Sequence[Mapping[str, Any]],
    source_digest: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    statement = {
        "kind": "statement",
        "localId": f"statement:{label}",
        "display": goal,
        "searchShape": {
            "declarationName": candidate,
            "role": "candidate-goal",
            "module": "Main",
            "requestGoal": goal,
        },
    }
    declaration = {
        "kind": "declaration",
        "localId": f"declaration:{label}",
        "display": candidate,
    }
    application = {
        "kind": "candidate-application",
        "localId": f"candidate-application:{label}",
        "display": candidate,
        "searchShape": _application_shape(
            candidate,
            goal,
            scratch,
            application_term,
            substitutions,
            residual_premises,
            discharged_hypotheses,
            local_context,
            source_digest,
        ),
    }
    check_subject = {"kind": "check-run", "localId": check_run_id}
    if scratch:
        result = "accepted" if status == "compiled" else "error"
        return (
            [application],
            [{
                "subjectRef": _compact(application),
                "result": result,
                "diagnostics": _diagnostics(status, failure_stage),
            }],
            [application, check_subject],
            "scratch-compilation",
        )
    if status == "rejected":
        return (
            [statement, declaration],
            [{
                "subjectRef": _compact(declaration),
                "result": "rejected",
                "diagnostics": _diagnostics(status, failure_stage),
            }],
            [statement, declaration, check_subject],
            "exact-candidate-elaboration",
        )
    return (
        [statement, declaration, application],
        [
            {"subjectRef": _compact(application), "result": "accepted", "diagnostics": []},
            {
                "subjectRef": _compact(statement),
                "result": (
                    "unchecked" if status == "applicable-with-residuals" else "accepted"
                ),
                "diagnostics": [],
            },
        ],
        [statement, declaration, application, check_subject],
        "exact-candidate-elaboration",
    )


def _fixture_residuals(
    status: str, residual_premises: Sequence[Mapping[str, Any]] | None
) -> list[dict[str, Any]]:
    if residual_premises is not None:
        return [dict(row) for row in residual_premises]
    if status == "applicable-with-residuals":
        return [{"typeDisplay": "True", "typeStructural": "True"}]
    return []


def _application_shape(
    candidate: str,
    goal: str,
    scratch: bool,
    application_term: str,
    substitutions: Sequence[Mapping[str, Any]],
    residual_premises: Sequence[Mapping[str, Any]],
    discharged_hypotheses: Sequence[Mapping[str, Any]],
    local_context: Sequence[Mapping[str, Any]],
    source_digest: str,
) -> dict[str, Any]:
    common = {
        "candidate": candidate,
        "applicationTerm": application_term,
        "localContext": [dict(row) for row in local_context],
    }
    if scratch:
        return {
            **common,
            "module": "Main",
            "goal": goal,
            "sourceDigest": source_digest,
        }
    return {
        **common,
        "substitutions": [dict(row) for row in substitutions],
        "residualPremises": [dict(row) for row in residual_premises],
        "dischargedHypotheses": [dict(row) for row in discharged_hypotheses],
    }


def semantic_receipt(
    label: str = "main",
    *,
    candidate: str | None = None,
    goal: str = "True",
    status: str = "accepted",
    authority_basis: str = "elaborator-check",
    completeness: str | None = None,
    scratch: bool = False,
    local_context: Sequence[dict[str, str]] = (),
) -> dict[str, Any]:
    """Return the exact receipt embedded by :func:`semantic_evidence`."""

    candidate = candidate or f"Main.{label}"
    if scratch:
        operation_outcome = "accepted" if status == "compiled" else "failed"
        authority_basis = "process-observation"
        completeness = "partial"
    else:
        operation_outcome = "rejected" if status == "rejected" else "accepted"
        completeness = completeness or (
            "partial" if status == "applicable-with-residuals" else "complete"
        )
    return build_evidence_receipt(
        subject={
            "module": "Main",
            "candidate": candidate,
            "goal": goal,
            "localContext": [dict(row) for row in local_context],
        },
        execution_binding="explicit-pinned",
        observation_state="live" if operation_outcome != "failed" else "failed",
        operation_outcome=operation_outcome,
        authority_basis=authority_basis,
        analysis_completeness=str(completeness),
        source_freshness="unknown",
        environment_match="exact",
        environment_ref=str(environment_artifact()["environmentRef"]),
        check_run_ref=check_ref(label),
    )


def _compact(subject: dict[str, Any]) -> dict[str, str]:
    return {"kind": str(subject["kind"]), "localId": str(subject["localId"])}


def _diagnostics(status: str, failure_stage: str) -> list[dict[str, Any]]:
    if status in {"accepted", "applicable-with-residuals", "compiled"}:
        return []
    scratch = status != "rejected"
    code = status if scratch else failure_stage
    return [
        {
            "stage": "scratch" if scratch else failure_stage,
            "code": code,
            "pointer": "/candidate",
            "message": status,
            "order": 0,
        }
    ]


__all__ = ["check_ref", "digest", "semantic_evidence", "semantic_receipt"]
