"""One-process Lean batch protocol for independent candidate outcomes.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import tempfile
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ladon.evidence_receipt import build_evidence_receipt
from ladon.lean_toolchain import LeanToolchainError, verify_toolchain_identities
from ladon.process_supervisor import run_bounded_target_process
from ladon.proofir_v3 import canonical_bytes, validate_envelope_batch
from ladon.semantic_candidate_limits import (
    MAX_SEMANTIC_BATCH_BYTES,
    MAX_SEMANTIC_BATCH_CANDIDATES,
    MAX_SEMANTIC_CANDIDATE_BYTES,
)
from ladon.semantic_candidate_worker import (
    DEFAULT_HELPER,
    SEMANTIC_BATCH_PROTOCOL,
    SEMANTIC_PROTOCOL,
    TRUSTED_TARGET_LIMITATION,
    UNIVERSE_POLICY,
    SemanticCandidateRequest,
    _accepted_artifacts,
    _check_run_subject,
    _compact,
    _digest_file,
    _digest_text,
    _envelope,
    _environment_artifact,
    _environment_source,
    _execution_context_ref,
    _goal_request_digest,
    _rejected_artifacts,
    _same_executable_identity,
    _valid_qualified_name,
    _validate_application_rows,
    _validate_worker_modules,
    _validate_worker_subject,
)
from ladon.semantic_lean_execution import (
    DirectLeanPreflightError,
    prepare_direct_lean_execution,
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
    terminal: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ladon-semantic-candidate-batch-result-v1",
            "operation": "check-candidates",
            "status": self.status,
            "terminal": self.terminal,
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
    helper_path = helper_path.resolve()
    _validate_batch_candidates(candidates)
    request_id = secrets.token_hex(16)
    probe_name = _batch_probe_name(request)
    source = _environment_source(request)
    with tempfile.TemporaryDirectory(prefix="ladon-semantic-batch-") as directory:
        probe_path = Path(directory) / "Probe.lean"
        probe_path.write_text(source, encoding="utf-8")
        try:
            execution = prepare_direct_lean_execution(
                request.repo_root, request.module, request.toolchain
            )
            helper_identity = _digest_file(helper_path)
            if request.toolchain is not None:
                verify_toolchain_identities(request.toolchain)
            process = runner(
                execution.command
                + (
                    "--run",
                    str(helper_path),
                    "--batch",
                    request.module,
                    str(probe_path),
                    goal_with_local_context(request.goal, request.local_context),
                    _goal_request_digest(request),
                    probe_name,
                    request_id,
                    _execution_context_ref(request),
                    *candidates,
                ),
                cwd=request.repo_root,
                env=execution.environment,
                timeout_seconds=request.timeout_seconds,
                max_output_bytes=request.max_output_bytes,
                max_rss_bytes=request.max_rss_bytes,
                cancel_event=cancel_event,
            )
            if request.toolchain is not None:
                verify_toolchain_identities(request.toolchain)
            if _digest_file(helper_path) != helper_identity:
                raise LeanToolchainError("semantic helper identity changed during execution")
        except LeanToolchainError as error:
            if isinstance(error, DirectLeanPreflightError):
                return SemanticCandidateBatchCheck(
                    "failed-checker",
                    diagnostic={"code": error.code, "message": str(error)},
                )
            return SemanticCandidateBatchCheck(
                "invalid-worker-output",
                diagnostic={"code": "toolchain-identity-changed", "message": str(error)},
            )
    return _interpret_batch_process(request, candidates, helper_path, process, request_id)


def _interpret_batch_process(
    request: SemanticCandidateRequest,
    candidates: Sequence[str],
    helper_path: Path,
    process: Any,
    request_id: str,
) -> SemanticCandidateBatchCheck:
    try:
        payload, terminal = _parse_batch_worker_payload(
            process.stdout, request, request_id, candidates
        )
    except (TypeError, ValueError) as error:
        return SemanticCandidateBatchCheck(
            "invalid-worker-output",
            diagnostic={"code": "invalid-batch-worker-output", "message": str(error)},
            elapsed_seconds=process.elapsed_seconds,
            peak_rss_bytes=process.peak_rss_bytes,
        )
    try:
        rows = _materialize_batch_rows(
            request,
            helper_path,
            process,
            payload,
            authoritative=terminal and process.succeeded,
        )
    except (OSError, TypeError, ValueError) as error:
        return SemanticCandidateBatchCheck(
            "invalid-worker-output",
            diagnostic={"code": "invalid-batch-evidence", "message": str(error)},
            elapsed_seconds=process.elapsed_seconds,
            peak_rss_bytes=process.peak_rss_bytes,
        )
    status = "available" if terminal and process.succeeded else ("partial" if rows else "failed")
    return SemanticCandidateBatchCheck(
        status,
        tuple(rows),
        diagnostic=(
            None
            if status == "available"
            else {
                **_process_diagnostic(process),
                **(
                    {"code": "malformed-batch-prefix", "message": payload["protocolDiagnostic"]}
                    if payload.get("protocolDiagnostic")
                    else {}
                ),
            }
        ),
        elapsed_seconds=process.elapsed_seconds,
        peak_rss_bytes=process.peak_rss_bytes,
        terminal=terminal and process.succeeded,
    )


def _validate_batch_candidates(candidates: Sequence[str]) -> None:
    if not candidates or len(candidates) > MAX_SEMANTIC_BATCH_CANDIDATES:
        raise ValueError("semantic candidate batch must contain between 1 and 100 candidates")
    if len(set(candidates)) != len(candidates) or any(
        not _valid_qualified_name(candidate) for candidate in candidates
    ):
        raise ValueError("semantic candidate batch contains invalid or duplicate candidates")
    encoded_sizes = [len(candidate.encode("utf-8")) for candidate in candidates]
    if (
        any(size > MAX_SEMANTIC_CANDIDATE_BYTES for size in encoded_sizes)
        or sum(encoded_sizes) > MAX_SEMANTIC_BATCH_BYTES
    ):
        raise ValueError("semantic candidate batch exceeds the supported transport byte cap")


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
) -> tuple[dict[str, Any], bool]:
    frames, decode_diagnostic = _decode_batch_frames(stdout)
    header = frames[0]
    _validate_batch_header(header, request, request_id)
    rows, terminal, prefix_diagnostic = _validated_batch_prefix(
        frames[1:], request_id, candidates, header["localContext"]
    )
    if decode_diagnostic:
        terminal = False
    payload = {**header, "rows": rows, "terminal": terminal}
    if decode_diagnostic or prefix_diagnostic:
        payload["protocolDiagnostic"] = decode_diagnostic or prefix_diagnostic
    return payload, terminal


def _decode_batch_frames(stdout: str) -> tuple[list[dict[str, Any]], str | None]:
    prefix = "LADON_FRAME "
    encoded = [line[len(prefix) :] for line in stdout.splitlines() if line.startswith(prefix)]
    if not encoded:
        raise ValueError("Lean semantic helper emitted no batch frames")
    frames: list[dict[str, Any]] = []
    diagnostic: str | None = None
    for encoded_frame in encoded:
        try:
            frame = json.loads(encoded_frame)
        except json.JSONDecodeError:
            if not frames:
                raise ValueError("Lean semantic helper emitted malformed batch JSON")
            diagnostic = "Lean semantic helper emitted malformed trailing batch JSON"
            break
        if not isinstance(frame, dict):
            if not frames:
                raise TypeError("Lean semantic helper emitted a non-object batch frame")
            diagnostic = "Lean semantic helper emitted a non-object trailing batch frame"
            break
        frames.append(frame)
    return frames, diagnostic


def _validate_batch_header(
    payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str
) -> None:
    expected = {
        "protocol",
        "frameVersion",
        "frameKind",
        "sequence",
        "terminal",
        "universePolicy",
        "requestId",
        "goalRequestDigest",
        "executionContextRef",
        "leanVersion",
        "leanCommit",
        "executablePath",
        "module",
        "probe",
        "importedModules",
        "localContext",
    }
    if set(payload) != expected or payload.get("frameKind") != "header":
        raise ValueError("Lean semantic helper returned an invalid batch header")
    _validate_batch_identity(payload, request, request_id)


def _validated_batch_prefix(
    frames: Sequence[Mapping[str, Any]],
    request_id: str,
    candidates: Sequence[str],
    local_context: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], bool, str | None]:
    rows: list[dict[str, Any]] = []
    terminal = False
    diagnostic: str | None = None
    for sequence, frame in enumerate(frames, start=1):
        try:
            _validate_prefix_frame(frame, request_id, sequence)
        except (TypeError, ValueError) as error:
            if not rows:
                raise
            diagnostic = str(error)
            break
        if frame["frameKind"] == "summary":
            try:
                _validate_batch_summary(frame, sequence, len(rows), len(candidates), len(frames))
            except ValueError:
                if rows:
                    diagnostic = "Lean semantic helper returned an invalid batch summary"
                    break
                raise
            terminal = True
            break
        if len(rows) >= len(candidates):
            if rows:
                diagnostic = "Lean semantic helper emitted more candidate frames than requested"
                break
            raise ValueError("Lean semantic helper emitted more candidate frames than requested")
        try:
            row = _validated_prefix_row(frame, candidates[len(rows)], local_context)
        except (TypeError, ValueError) as error:
            if not rows:
                raise
            diagnostic = str(error)
            break
        rows.append(dict(row))
    return rows, terminal, diagnostic


def _validate_batch_summary(
    frame: Mapping[str, Any], sequence: int, completed: int, total: int, frame_count: int
) -> None:
    if (
        sequence != total + 1
        or frame["completed"] != completed
        or frame["total"] != total
        or sequence != frame_count
    ):
        raise ValueError("Lean semantic helper returned an invalid batch summary")


def _validated_prefix_row(
    frame: Mapping[str, Any], candidate: str, local_context: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    row = frame["row"]
    _validate_batch_row(row, candidate, local_context)
    return dict(row)


def _validate_prefix_frame(frame: Mapping[str, Any], request_id: str, sequence: int) -> None:
    common = {"protocol", "frameVersion", "frameKind", "sequence", "terminal", "requestId"}
    kind = frame.get("frameKind")
    expected = common | ({"row"} if kind == "candidate" else {"completed", "total"})
    if (
        set(frame) != expected
        or frame.get("protocol") != SEMANTIC_BATCH_PROTOCOL
        or frame.get("frameVersion") != 1
        or frame.get("requestId") != request_id
        or frame.get("sequence") != sequence
        or frame.get("terminal") is not (kind == "summary")
        or kind not in {"candidate", "summary"}
    ):
        raise ValueError("Lean semantic helper returned an invalid sequenced batch frame")


def _validate_batch_identity(
    payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str
) -> None:
    _validate_batch_required_fields(payload)
    _validate_batch_frame(payload, request, request_id)
    _validate_batch_execution_identity(payload)
    _validate_batch_toolchain_identity(payload, request)
    _validate_batch_semantic_population(payload, request)


def _validate_batch_required_fields(payload: Mapping[str, Any]) -> None:
    required = {
        "protocol",
        "frameVersion",
        "frameKind",
        "sequence",
        "terminal",
        "universePolicy",
        "requestId",
        "goalRequestDigest",
        "leanVersion",
        "leanCommit",
        "executablePath",
        "module",
        "probe",
        "importedModules",
        "localContext",
    }
    if not required <= set(payload):
        raise ValueError("Lean semantic helper omitted required batch evidence fields")


def _validate_batch_frame(
    payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str
) -> None:
    if payload.get("protocol") != SEMANTIC_BATCH_PROTOCOL or payload.get("requestId") != request_id:
        raise ValueError("Lean semantic helper returned an invalid batch identity")
    if payload.get("executionContextRef") != _execution_context_ref(request):
        raise ValueError("Lean semantic helper returned a mismatched execution context")
    if payload.get("goalRequestDigest") != _goal_request_digest(request):
        raise ValueError("Lean semantic helper returned a mismatched goal request digest")
    if (
        payload.get("frameVersion") != 1
        or payload.get("sequence") != 0
        or payload.get("terminal") is not False
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


def _validate_batch_toolchain_identity(
    payload: Mapping[str, Any], request: SemanticCandidateRequest
) -> None:
    if request.toolchain is None:
        return
    if request.toolchain.selection_mode == "explicit" and not _same_executable_identity(
        Path(str(payload["executablePath"])), request.toolchain
    ):
        raise ValueError("Lean semantic helper returned a foreign batch executable path")
    expected = request.toolchain.pin_content.rsplit(":v", 1)[-1]
    versions = set(
        re.findall(
            r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?)(?![0-9])",
            str(payload["leanVersion"]),
        )
    )
    if versions != {expected}:
        raise ValueError("Lean semantic helper returned an unbound batch Lean version")
    if (
        request.toolchain.lean_commit is not None
        and str(payload.get("leanCommit", "")).lower() != request.toolchain.lean_commit
    ):
        raise ValueError("Lean semantic helper returned an unbound batch Lean commit")


def _validate_batch_semantic_population(
    payload: Mapping[str, Any], request: SemanticCandidateRequest
) -> None:
    _validate_worker_subject(payload.get("probe"), "probe", _batch_probe_name(request))
    _validate_worker_modules(payload.get("importedModules"), request.module)
    _validate_application_rows(
        {
            "substitutions": [],
            "dischargedHypotheses": [],
            "residualPremises": [],
            "localContext": payload.get("localContext"),
        }
    )
    validate_observed_local_context(payload["localContext"], request.local_context)


def _validate_batch_rows(rows: list[Any], candidates: Sequence[str]) -> None:
    names = [row.get("candidate") for row in rows if isinstance(row, dict)]
    if names != list(candidates):
        raise ValueError("Lean semantic helper returned a reordered or incomplete candidate batch")
    for row, candidate in zip(rows, candidates):
        _validate_batch_row(row, candidate)


def _validate_batch_row(
    row: Any, candidate: str, local_context: Sequence[Mapping[str, Any]] = ()
) -> None:
    _validate_batch_row_shape(row, candidate)
    _validate_batch_row_evidence(row, candidate, local_context)


def _validate_batch_row_shape(row: Any, candidate: str) -> None:
    fields = {
        "candidate",
        "status",
        "candidateSubject",
        "applicationTerm",
        "dischargedHypotheses",
        "substitutions",
        "residualPremises",
        "failureStage",
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
    if not isinstance(row["failureStage"], str):
        raise TypeError("Lean semantic helper returned an invalid candidate failure stage")
    if not isinstance(row["applicationTerm"], str):
        raise TypeError("Lean semantic helper returned an invalid candidate application term")


def _validate_batch_row_evidence(
    row: Mapping[str, Any], candidate: str, local_context: Sequence[Mapping[str, Any]] = ()
) -> None:
    _validate_application_rows(
        {
            "substitutions": row["substitutions"],
            "dischargedHypotheses": row["dischargedHypotheses"],
            "residualPremises": row["residualPremises"],
            "localContext": list(local_context),
        }
    )
    if row["status"] == "rejected":
        _validate_rejected_row(row)
        return
    if row["failureStage"]:
        raise ValueError("accepted candidate row carries a failure stage")
    _validate_worker_subject(row["candidateSubject"], "candidate", candidate)
    if not row["applicationTerm"]:
        raise ValueError("accepted candidate row omits its exact application term")
    if bool(row["residualPremises"]) != (row["status"] == "applicable-with-residuals"):
        raise ValueError("candidate status disagrees with residual premises")


def _validate_rejected_row(row: Mapping[str, Any]) -> None:
    if (
        row["candidateSubject"] is not None
        or row["applicationTerm"]
        or row["dischargedHypotheses"]
        or row["substitutions"]
        or row["residualPremises"]
    ):
        raise ValueError("rejected candidate row carries accepted evidence")
    if row["failureStage"] not in {
        "candidate-name-invalid",
        "candidate-not-found",
        "application-rejected",
    }:
        raise ValueError("rejected candidate row omits a structured failure stage")


def _materialize_batch_rows(
    request: SemanticCandidateRequest,
    helper_path: Path,
    process: Any,
    payload: Mapping[str, Any],
    *,
    authoritative: bool,
) -> list[dict[str, Any]]:
    environment = _environment_artifact(request.repo_root, payload, request.toolchain)
    if not authoritative:
        return [
            _materialize_partial_row(
                request, helper_path, process, payload["localContext"], environment, row
            )
            for row in payload["rows"]
        ]
    return [
        _materialize_batch_row(request, helper_path, process, payload, environment, row)
        for row in payload["rows"]
    ]


def _materialize_partial_row(
    request: SemanticCandidateRequest,
    helper_path: Path,
    process: Any,
    observed_context: Sequence[Mapping[str, Any]],
    environment: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_request = replace(request, candidate=str(row["candidate"]))
    check_ref = (
        "check:"
        + _digest_text(
            canonical_bytes(
                {
                    "environmentRef": environment["environmentRef"],
                    "candidate": row["candidate"],
                    "goal": request.goal,
                    "localContext": [dict(item) for item in request.local_context],
                    "status": row["status"],
                    "applicationTerm": row.get("applicationTerm"),
                    "substitutions": row.get("substitutions", []),
                    "residualPremises": row.get("residualPremises", []),
                    "dischargedHypotheses": row.get("dischargedHypotheses", []),
                    "processOutcome": _partial_process_outcome(process),
                    "batchTerminal": False,
                }
            ).decode()
        )[7:]
    )
    receipt = _prefix_receipt(
        candidate_request,
        str(environment["environmentRef"]),
        check_ref,
        str(row["status"]),
        local_context=observed_context,
    )
    observed_row = {
        **row,
        "localContext": [dict(item) for item in observed_context],
        "processOutcome": _partial_process_outcome(process),
    }
    check_artifact = _batch_check_artifact(
        candidate_request,
        environment,
        check_ref,
        observed_row,
        receipt,
        helper_path=helper_path,
        process=process,
    )
    validate_envelope_batch([dict(environment), check_artifact])
    return {
        **observed_row,
        "callerLocalContext": [dict(item) for item in request.local_context],
        "batchTerminal": False,
        "environmentRef": environment["environmentRef"],
        "checkRunRef": check_ref,
        "evidenceReceipt": receipt,
        "artifacts": [dict(environment), check_artifact],
    }


def _prefix_receipt(
    request: SemanticCandidateRequest,
    environment_ref: str,
    check_ref: str,
    status: str,
    *,
    local_context: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    explicit = request.toolchain is not None and request.toolchain.selection_mode == "explicit"
    return build_evidence_receipt(
        subject={
            "module": request.module,
            "candidate": request.candidate,
            "goal": request.goal,
            "localContext": _receipt_local_context(local_context or request.local_context),
        },
        execution_binding="explicit-pinned" if explicit else "ambient-observed",
        observation_state="live",
        operation_outcome="rejected" if status == "rejected" else "accepted",
        authority_basis="process-observation",
        analysis_completeness="partial",
        environment_match=(
            "exact"
            if request.toolchain is not None and request.toolchain.lean_commit is not None
            else "unknown"
        ),
        environment_ref=environment_ref,
        check_run_ref=check_ref,
        limitations=(
            TRUSTED_TARGET_LIMITATION,
            "Batch terminated before its completeness summary; only this validated prefix row is observed.",
        ),
    )


def _process_diagnostic(process: Any) -> dict[str, str]:
    if process.timed_out:
        code = "batch-timeout"
    elif process.output_limited:
        code = "batch-output-limit"
    elif process.memory_limited:
        code = "batch-memory-limit"
    elif process.returncode != 0:
        code = "batch-worker-failed"
    else:
        code = "batch-terminal-summary-missing"
    return {"code": code, "message": (process.stderr or "").strip() or code}


def _partial_process_outcome(process: Any) -> str:
    if process.timed_out:
        return "timeout"
    if process.output_limited:
        return "output-limited"
    if process.memory_limited:
        return "memory-limited"
    if process.returncode != 0:
        return "failed-checker"
    return "summary-missing"


def _receipt_local_context(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "name": str(row.get("userName", row.get("name", ""))),
            "type": str(row.get("typeDisplay", row.get("type", ""))),
        }
        for row in rows
    ]


def _batch_result_diagnostics(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    if row.get("diagnostic"):
        diagnostics.append(
            {
                "stage": str(row.get("failureStage") or "candidate-check"),
                "code": str(row.get("failureStage") or "candidate-rejected"),
                "pointer": "/candidate",
                "message": str(row["diagnostic"]),
                "order": len(diagnostics),
            }
        )
    if row.get("processOutcome"):
        diagnostics.append(
            {
                "stage": "batch-process",
                "code": str(row["processOutcome"]),
                "pointer": "/process",
                "message": "Candidate result belongs to a non-terminal batch observation.",
                "order": len(diagnostics),
            }
        )
    return diagnostics


def _materialize_batch_row(
    request: SemanticCandidateRequest,
    helper_path: Path,
    process: Any,
    payload: Mapping[str, Any],
    environment: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_request = replace(request, candidate=str(row["candidate"]))
    observed_row = {**row, "localContext": list(payload["localContext"])}
    if row["status"] != "rejected":
        single = _single_payload(payload, row)
        artifacts = _accepted_artifacts(
            candidate_request,
            helper_path,
            process,
            single,
            environment_artifact=environment,
        )
        validate_envelope_batch(list(artifacts))
        receipt = artifacts[1]["extensions"]["ladon.process-observation/v1"]["evidenceReceipt"]
        return {
            **dict(row),
            "callerLocalContext": [dict(item) for item in request.local_context],
            "environmentRef": environment["environmentRef"],
            "checkRunRef": artifacts[1]["payload"]["checkRunId"],
            "evidenceReceipt": receipt,
            "artifacts": list(artifacts),
        }
    rejection_payload = {
        "protocol": SEMANTIC_PROTOCOL,
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": payload["universePolicy"],
        "requestId": payload["requestId"],
        "executionContextRef": payload["executionContextRef"],
        "leanVersion": payload["leanVersion"],
        "leanCommit": payload["leanCommit"],
        "executablePath": payload["executablePath"],
        "module": payload["module"],
        "probe": payload["probe"],
        "candidateName": row["candidate"],
        "status": "rejected",
        "failureStage": row["failureStage"],
        "diagnostic": row["diagnostic"],
        "importedModules": payload["importedModules"],
        "localContext": payload["localContext"],
    }
    artifacts, receipt = _rejected_artifacts(
        candidate_request,
        helper_path,
        process,
        rejection_payload,
        helper_identity=_digest_file(helper_path),
        environment_artifact=environment,
    )
    validate_envelope_batch(list(artifacts))
    return {
        **observed_row,
        "callerLocalContext": [dict(item) for item in request.local_context],
        "environmentRef": artifacts[0]["environmentRef"],
        "checkRunRef": artifacts[1]["payload"]["checkRunId"],
        "evidenceReceipt": receipt,
        "artifacts": list(artifacts),
    }


def _batch_check_artifact(
    request: SemanticCandidateRequest,
    environment: Mapping[str, Any],
    check_ref: str,
    row: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    helper_path: Path | None = None,
    process: Any | None = None,
) -> dict[str, Any]:
    authority_basis = str(receipt.get("authorityBasis", "process-observation"))
    env_ref = str(environment["environmentRef"])
    statement = _synthetic_subject("statement", request.goal)
    statement["searchShape"] = {
        "declarationName": request.candidate,
        "role": "candidate-goal",
        "module": request.module,
        "requestGoal": request.goal,
    }
    declaration = _synthetic_subject("declaration", request.candidate)
    context_rows = row.get("localContext") or row.get("callerLocalContext") or []
    context = _synthetic_subject("local-context", json.dumps(context_rows, sort_keys=True))
    context["searchShape"] = {
        "orderedLocals": context_rows,
        "origin": "observed-prefix",
    }
    application_term = row.get("applicationTerm")
    application_display = str(application_term or request.candidate)
    application = _synthetic_subject("candidate-application", application_display)
    application["searchShape"] = {
        "candidate": request.candidate,
        "applicationTerm": application_term,
        "substitutions": row.get("substitutions", []),
        "residualPremises": row.get("residualPremises", []),
        "dischargedHypotheses": row.get("dischargedHypotheses", []),
        "localContext": context_rows,
        "processOutcome": row.get("processOutcome"),
    }
    residual_subjects = [
        _synthetic_subject("statement", str(item.get("typeDisplay", "")))
        for item in row.get("residualPremises", [])
    ]
    term_subjects = [
        _synthetic_subject("term", str(item.get("termDisplay", "")))
        for item in row.get("substitutions", [])
    ]
    input_subjects = [
        statement,
        declaration,
        context,
        application,
        *residual_subjects,
        *term_subjects,
    ]
    subjects = [*input_subjects, _check_run_subject(check_ref)]
    digest = "sha256:" + hashlib.sha256(b"").hexdigest()
    helper_digest = _digest_file(helper_path) if helper_path is not None else digest
    executable_digest = (
        _digest_file(Path(str(process.command[2])))
        if process is not None
        and len(process.command) > 2
        and Path(str(process.command[2])).is_file()
        else digest
    )
    artifact = _envelope(
        "proofir.check-run",
        env_ref,
        subjects,
        {
            "checkRunId": check_ref,
            "checker": {
                "name": "Lean",
                "version": "batch-protocol",
                "implementationDigest": helper_digest,
                "executableDigest": executable_digest,
            },
            "operation": "exact-candidate-elaboration",
            "inputs": {
                "environmentRef": env_ref,
                "subjectRefs": [_compact(subject) for subject in input_subjects],
                "artifactRefs": [str(environment["artifactId"])],
            },
            "results": [
                {
                    "subjectRef": _compact(application),
                    "result": "rejected" if row["status"] == "rejected" else "accepted",
                    "diagnostics": _batch_result_diagnostics(row),
                }
            ],
            "outputs": {
                "stdoutDigest": (_digest_text(process.stdout) if process is not None else digest),
                "stderrDigest": (_digest_text(process.stderr) if process is not None else digest),
            },
            "bounds": {
                "timeoutMs": max(1, int(request.timeout_seconds * 1000)),
                "maxOutputBytes": request.max_output_bytes,
            },
            "guarantee": {
                "scope": ("route" if authority_basis == "elaborator-check" else "process-exit"),
                "statement": "This artifact records one bounded batch candidate observation.",
                "authorityBasis": authority_basis,
            },
        },
        extensions={"ladon.process-observation/v1": {"evidenceReceipt": dict(receipt)}},
    )
    return artifact.to_dict()


def _synthetic_subject(kind: str, display: str) -> dict[str, Any]:
    digest = "sha256:" + hashlib.sha256(display.encode()).hexdigest()
    return {
        "kind": kind,
        "localId": f"{kind}:{digest}",
        "fingerprint": {"scheme": {"name": "batch-observation", "version": "1"}, "digest": digest},
        "display": display,
    }


def _single_payload(payload: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "protocol": SEMANTIC_PROTOCOL,
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": payload["universePolicy"],
        "requestId": payload["requestId"],
        "executionContextRef": payload["executionContextRef"],
        "leanVersion": payload["leanVersion"],
        "leanCommit": payload["leanCommit"],
        "executablePath": payload["executablePath"],
        "module": payload["module"],
        "probe": payload["probe"],
        "candidate": row["candidateSubject"],
        "applicationTerm": row["applicationTerm"],
        "dischargedHypotheses": row["dischargedHypotheses"],
        "importedModules": payload["importedModules"],
        "substitutions": row["substitutions"],
        "residualPremises": row["residualPremises"],
        "localContext": payload["localContext"],
    }


__all__ = ["SemanticCandidateBatchCheck", "check_semantic_candidates"]
