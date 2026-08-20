"""One-process Lean batch protocol for independent candidate outcomes."""

from __future__ import annotations

import secrets
import tempfile
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.process_supervisor import run_bounded_target_process
from ladon.proofir_v3 import canonical_bytes
from ladon.semantic_candidate_worker import (
    DEFAULT_HELPER,
    SEMANTIC_BATCH_PROTOCOL,
    SemanticCandidateRequest,
    _decode_single_frame,
    _digest_text,
    _environment_source,
    _valid_qualified_name,
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
            "resourceAccounting": {"elapsedSeconds": round(self.elapsed_seconds, 6), "peakRssBytes": self.peak_rss_bytes},
            "nonclaims": ["Each row is one bounded Lean observation, not an unqualified theorem verdict."],
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
            command + ("--run", str(helper_path), "--batch", request.module, str(probe_path), request.goal, probe_name, request_id, *candidates),
            cwd=request.repo_root,
            env=(request.toolchain.environment if request.toolchain else None),
            timeout_seconds=request.timeout_seconds,
            max_output_bytes=request.max_output_bytes,
            max_rss_bytes=request.max_rss_bytes,
            cancel_event=cancel_event,
        )
    if not process.succeeded:
        return SemanticCandidateBatchCheck("failed", diagnostic={"code": "batch-worker-failed", "message": (process.stderr or process.stdout).strip()}, elapsed_seconds=process.elapsed_seconds, peak_rss_bytes=process.peak_rss_bytes)
    try:
        payload = _parse_batch_worker_payload(process.stdout, request, request_id, candidates)
    except (TypeError, ValueError) as error:
        return SemanticCandidateBatchCheck("invalid-worker-output", diagnostic={"code": "invalid-batch-worker-output", "message": str(error)}, elapsed_seconds=process.elapsed_seconds, peak_rss_bytes=process.peak_rss_bytes)
    return SemanticCandidateBatchCheck("available", tuple(payload["rows"]), elapsed_seconds=process.elapsed_seconds, peak_rss_bytes=process.peak_rss_bytes)


def _validate_batch_candidates(candidates: Sequence[str]) -> None:
    if not candidates or len(candidates) > 100:
        raise ValueError("semantic candidate batch must contain between 1 and 100 candidates")
    if len(set(candidates)) != len(candidates) or any(not _valid_qualified_name(candidate) for candidate in candidates):
        raise ValueError("semantic candidate batch contains invalid or duplicate candidates")


def _batch_probe_name(request: SemanticCandidateRequest) -> str:
    identity = _digest_text(canonical_bytes({"module": request.module, "goal": request.goal, "batch": True}).decode("utf-8"))
    return "ladonSemanticBatchProbe_" + identity[7:23]


def _parse_batch_worker_payload(stdout: str, request: SemanticCandidateRequest, request_id: str, candidates: Sequence[str]) -> dict[str, Any]:
    payload = _decode_single_frame(stdout)
    _validate_batch_identity(payload, request, request_id)
    _validate_batch_rows(payload["rows"], candidates)
    return payload


def _validate_batch_identity(payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str) -> None:
    if payload.get("protocol") != SEMANTIC_BATCH_PROTOCOL or payload.get("requestId") != request_id:
        raise ValueError("Lean semantic helper returned an invalid batch identity")
    if payload.get("frameVersion") != 1 or payload.get("terminal") is not True or payload.get("module") != request.module:
        raise ValueError("Lean semantic helper returned an invalid batch population")
    if not isinstance(payload.get("rows"), list):
        raise TypeError("Lean semantic helper returned non-list batch rows")


def _validate_batch_rows(rows: list[Any], candidates: Sequence[str]) -> None:
    names = [row.get("candidate") for row in rows if isinstance(row, dict)]
    if names != list(candidates):
        raise ValueError("Lean semantic helper returned a reordered or incomplete candidate batch")
    allowed = {"accepted", "applicable-with-residuals", "rejected"}
    if any(not isinstance(row, dict) or row.get("status") not in allowed for row in rows):
        raise ValueError("Lean semantic helper returned an invalid candidate outcome")


__all__ = ["SemanticCandidateBatchCheck", "check_semantic_candidates"]
