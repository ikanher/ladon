"""One-process Lean batch protocol for independent candidate outcomes."""

from __future__ import annotations

import secrets
import tempfile
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ladon.evidence_receipt import build_evidence_receipt
from ladon.process_supervisor import run_bounded_target_process
from ladon.proofir_v3 import canonical_bytes, validate_envelope_batch
from ladon.semantic_candidate_worker import (
    DEFAULT_HELPER,
    SEMANTIC_BATCH_PROTOCOL,
    SEMANTIC_PROTOCOL,
    UNIVERSE_POLICY,
    SemanticCandidateRequest,
    _accepted_artifacts,
    _decode_single_frame,
    _digest_text,
    _environment_artifact,
    _environment_source,
    _valid_qualified_name,
    _validate_application_rows,
    _validate_worker_modules,
    _validate_worker_subject,
)
from ladon.semantic_local_context import (
    goal_with_local_context,
    validate_observed_local_context,
)

ProcessRunner = Any


@dataclass(frozen=True)
class SemanticCandidateBatchCheck:
    status: str
    rows: tuple[Mapping[str, Any], ...] = ()
    diagnostic: Mapping[str, Any] | None = None
    elapsed_seconds: float = 0.0
    peak_rss_bytes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ladon-semantic-candidate-batch-result-v1",
            "operation": "check-candidates",
            "status": self.status,
            "rows": [dict(row) for row in self.rows],
            "diagnostic": dict(self.diagnostic) if self.diagnostic else None,
            "resourceAccounting": {
                "elapsedSeconds": round(self.elapsed_seconds, 6),
                "peakRssBytes": self.peak_rss_bytes,
            },
            "nonclaims": [
                "Each row is one bounded Lean observation, not an unqualified theorem verdict."
            ],
        }


def check_semantic_candidates(
    request: SemanticCandidateRequest,
    candidates: Sequence[str],
    *,
    helper_path: Path = DEFAULT_HELPER,
    runner: ProcessRunner = run_bounded_target_process,
    cancel_event: threading.Event | None = None,
) -> SemanticCandidateBatchCheck:
    _validate_batch_candidates(candidates)
    request_id = secrets.token_hex(16)
    probe_name = _batch_probe_name(request)
    source = _environment_source(request)
    with tempfile.TemporaryDirectory(prefix="ladon-semantic-batch-") as directory:
        probe_path = Path(directory) / "Probe.lean"
        probe_path.write_text(source, encoding="utf-8")
        command = (
            (str(request.toolchain.lake_path), "env", str(request.toolchain.lean_path))
            if request.toolchain is not None
            else ("lake", "env", "lean")
        )
        process = runner(
            command
            + (
                "--run",
                str(helper_path),
                "--batch",
                request.module,
                str(probe_path),
                goal_with_local_context(request.goal, request.local_context),
                probe_name,
                request_id,
                *candidates,
            ),
            cwd=request.repo_root,
            env=(request.toolchain.environment if request.toolchain else None),
            timeout_seconds=request.timeout_seconds,
            max_output_bytes=request.max_output_bytes,
            max_rss_bytes=request.max_rss_bytes,
            cancel_event=cancel_event,
        )
    if not process.succeeded:
        return SemanticCandidateBatchCheck(
            "failed",
            diagnostic={
                "code": "batch-worker-failed",
                "message": (process.stderr or process.stdout).strip(),
            },
            elapsed_seconds=process.elapsed_seconds,
            peak_rss_bytes=process.peak_rss_bytes,
        )
    try:
        payload = _parse_batch_worker_payload(process.stdout, request, request_id, candidates)
    except (TypeError, ValueError) as error:
        return SemanticCandidateBatchCheck(
            "invalid-worker-output",
            diagnostic={"code": "invalid-batch-worker-output", "message": str(error)},
            elapsed_seconds=process.elapsed_seconds,
            peak_rss_bytes=process.peak_rss_bytes,
        )
    try:
        rows = _materialize_batch_rows(request, helper_path, process, payload)
    except (OSError, TypeError, ValueError) as error:
        return SemanticCandidateBatchCheck(
            "invalid-worker-output",
            diagnostic={"code": "invalid-batch-evidence", "message": str(error)},
            elapsed_seconds=process.elapsed_seconds,
            peak_rss_bytes=process.peak_rss_bytes,
        )
    return SemanticCandidateBatchCheck(
        "available",
        tuple(rows),
        elapsed_seconds=process.elapsed_seconds,
        peak_rss_bytes=process.peak_rss_bytes,
    )


def _validate_batch_candidates(candidates: Sequence[str]) -> None:
    if not candidates or len(candidates) > 100:
        raise ValueError("semantic candidate batch must contain between 1 and 100 candidates")
    if len(set(candidates)) != len(candidates) or any(
        not _valid_qualified_name(candidate) for candidate in candidates
    ):
        raise ValueError("semantic candidate batch contains invalid or duplicate candidates")


def _batch_probe_name(request: SemanticCandidateRequest) -> str:
    identity = _digest_text(
        canonical_bytes(
            {
                "module": request.module,
                "goal": request.goal,
                "localContext": [dict(row) for row in request.local_context],
                "batch": True,
            }
        ).decode("utf-8")
    )
    return "ladonSemanticBatchProbe_" + identity[7:23]


def _parse_batch_worker_payload(
    stdout: str, request: SemanticCandidateRequest, request_id: str, candidates: Sequence[str]
) -> dict[str, Any]:
    payload = _decode_single_frame(stdout)
    _validate_batch_identity(payload, request, request_id)
    _validate_batch_rows(payload["rows"], candidates)
    return payload


def _validate_batch_identity(
    payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str
) -> None:
    _validate_batch_required_fields(payload)
    _validate_batch_frame(payload, request, request_id)
    _validate_batch_execution_identity(payload)
    _validate_batch_semantic_population(payload, request)


def _validate_batch_required_fields(payload: Mapping[str, Any]) -> None:
    required = {
        "protocol",
        "frameVersion",
        "sequence",
        "terminal",
        "universePolicy",
        "requestId",
        "leanVersion",
        "leanCommit",
        "executablePath",
        "module",
        "probe",
        "importedModules",
        "rows",
        "localContext",
    }
    if not required <= set(payload):
        raise ValueError("Lean semantic helper omitted required batch evidence fields")


def _validate_batch_frame(
    payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str
) -> None:
    if payload.get("protocol") != SEMANTIC_BATCH_PROTOCOL or payload.get("requestId") != request_id:
        raise ValueError("Lean semantic helper returned an invalid batch identity")
    if (
        payload.get("frameVersion") != 1
        or payload.get("sequence") != 0
        or payload.get("terminal") is not True
        or payload.get("module") != request.module
    ):
        raise ValueError("Lean semantic helper returned an invalid batch population")
    if payload.get("universePolicy") != UNIVERSE_POLICY:
        raise ValueError("Lean semantic helper returned an unsupported batch universe policy")


def _validate_batch_execution_identity(payload: Mapping[str, Any]) -> None:
    if not all(
        isinstance(payload.get(field), str) and payload[field]
        for field in ("leanVersion", "leanCommit", "executablePath")
    ):
        raise ValueError("Lean semantic helper returned invalid batch execution identity")
    if not isinstance(payload.get("rows"), list):
        raise TypeError("Lean semantic helper returned non-list batch rows")


def _validate_batch_semantic_population(
    payload: Mapping[str, Any], request: SemanticCandidateRequest
) -> None:
    _validate_worker_subject(payload.get("probe"), "probe", _batch_probe_name(request))
    _validate_worker_modules(payload.get("importedModules"), request.module)
    _validate_application_rows(
        {"substitutions": [], "residualPremises": [], "localContext": payload.get("localContext")}
    )
    validate_observed_local_context(payload["localContext"], request.local_context)


def _validate_batch_rows(rows: list[Any], candidates: Sequence[str]) -> None:
    names = [row.get("candidate") for row in rows if isinstance(row, dict)]
    if names != list(candidates):
        raise ValueError("Lean semantic helper returned a reordered or incomplete candidate batch")
    for row, candidate in zip(rows, candidates):
        _validate_batch_row(row, candidate)


def _validate_batch_row(row: Any, candidate: str) -> None:
    _validate_batch_row_shape(row, candidate)
    _validate_batch_row_evidence(row, candidate)


def _validate_batch_row_shape(row: Any, candidate: str) -> None:
    fields = {
        "candidate",
        "status",
        "candidateSubject",
        "applicationTerm",
        "substitutions",
        "residualPremises",
        "diagnostic",
    }
    if not isinstance(row, dict) or set(row) != fields:
        raise ValueError("Lean semantic helper returned an invalid candidate row shape")
    if row["candidate"] != candidate or row["status"] not in {
        "accepted",
        "applicable-with-residuals",
        "rejected",
    }:
        raise ValueError("Lean semantic helper returned an invalid candidate outcome")
    if not isinstance(row["diagnostic"], str):
        raise TypeError("Lean semantic helper returned an invalid candidate diagnostic")
    if not isinstance(row["applicationTerm"], str):
        raise TypeError("Lean semantic helper returned an invalid candidate application term")


def _validate_batch_row_evidence(row: Mapping[str, Any], candidate: str) -> None:
    _validate_application_rows(
        {
            "substitutions": row["substitutions"],
            "residualPremises": row["residualPremises"],
            "localContext": [],
        }
    )
    if row["status"] == "rejected":
        _validate_rejected_row(row)
        return
    _validate_worker_subject(row["candidateSubject"], "candidate", candidate)
    if not row["applicationTerm"]:
        raise ValueError("accepted candidate row omits its exact application term")
    if bool(row["residualPremises"]) != (row["status"] == "applicable-with-residuals"):
        raise ValueError("candidate status disagrees with residual premises")


def _validate_rejected_row(row: Mapping[str, Any]) -> None:
    if (
        row["candidateSubject"] is not None
        or row["applicationTerm"]
        or row["substitutions"]
        or row["residualPremises"]
    ):
        raise ValueError("rejected candidate row carries accepted evidence")


def _materialize_batch_rows(
    request: SemanticCandidateRequest,
    helper_path: Path,
    process: Any,
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    environment = _environment_artifact(request.repo_root, payload, request.toolchain)
    return [
        _materialize_batch_row(request, helper_path, process, payload, environment, row)
        for row in payload["rows"]
    ]


def _materialize_batch_row(
    request: SemanticCandidateRequest,
    helper_path: Path,
    process: Any,
    payload: Mapping[str, Any],
    environment: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_request = replace(request, candidate=str(row["candidate"]))
    if row["status"] != "rejected":
        single = _single_payload(payload, row)
        artifacts = _accepted_artifacts(candidate_request, helper_path, process, single)
        validate_envelope_batch(list(artifacts))
        receipt = artifacts[1]["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"]
        return {
            **dict(row),
            "environmentRef": environment["environmentRef"],
            "checkRunRef": artifacts[1]["payload"]["checkRunId"],
            "evidenceReceipt": receipt,
            "artifacts": list(artifacts),
        }
    check_ref = (
        "check:"
        + _digest_text(
            canonical_bytes(
                {
                    "environmentRef": environment["environmentRef"],
                    "candidate": row["candidate"],
                    "diagnostic": row["diagnostic"],
                }
            ).decode()
        )[7:]
    )
    receipt = _rejected_receipt(candidate_request, str(environment["environmentRef"]), check_ref)
    return {
        **dict(row),
        "environmentRef": environment["environmentRef"],
        "checkRunRef": check_ref,
        "evidenceReceipt": receipt,
        "artifacts": [dict(environment)],
    }


def _single_payload(payload: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "protocol": SEMANTIC_PROTOCOL,
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": payload["universePolicy"],
        "requestId": payload["requestId"],
        "leanVersion": payload["leanVersion"],
        "leanCommit": payload["leanCommit"],
        "executablePath": payload["executablePath"],
        "module": payload["module"],
        "probe": payload["probe"],
        "candidate": row["candidateSubject"],
        "applicationTerm": row["applicationTerm"],
        "importedModules": payload["importedModules"],
        "substitutions": row["substitutions"],
        "residualPremises": row["residualPremises"],
        "localContext": payload["localContext"],
    }


def _rejected_receipt(
    request: SemanticCandidateRequest, environment_ref: str, check_ref: str
) -> dict[str, Any]:
    binding = "ambient-observed"
    environment_match = "unknown"
    if request.toolchain is not None:
        binding = (
            "explicit-pinned"
            if request.toolchain.selection_mode == "explicit"
            else "ambient-observed"
        )
        environment_match = "exact"
    return build_evidence_receipt(
        subject={
            "module": request.module,
            "candidate": request.candidate,
            "goal": request.goal,
            "localContext": [dict(row) for row in request.local_context],
        },
        execution_binding=binding,
        observation_state="live",
        operation_outcome="rejected",
        authority_basis="elaborator-check",
        analysis_completeness="complete",
        environment_match=environment_match,
        environment_ref=environment_ref,
        check_run_ref=check_ref,
        limitations=("Candidate rejection does not establish theorem falsehood.",),
    )


__all__ = ["SemanticCandidateBatchCheck", "check_semantic_candidates"]
