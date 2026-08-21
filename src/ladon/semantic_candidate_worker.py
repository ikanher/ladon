"""Explicit, supervised Lean candidate checking with native ProofIR output.

The Lean helper reports only environment-scoped semantic facts.  This module
observes the process boundary, hashes the exact helper/executable/output bytes,
and then creates the check-run and derivation artifacts.  A failed or bounded
run never publishes accepted evidence.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import tempfile
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.evidence_receipt import build_evidence_receipt
from ladon.lean_toolchain import (
    LeanToolchainContext,
    LeanToolchainError,
    verify_toolchain_identities,
)
from ladon.process_supervisor import ProcessResult, run_bounded_target_process
from ladon.proofir_fingerprint_registry import SCHEMES
from ladon.proofir_result_dimensions import derive_analysis_completeness
from ladon.proofir_v3 import (
    ProofIRV3Artifact,
    canonical_bytes,
    make_envelope,
    validate_envelope_batch,
)
from ladon.semantic_candidate_protocol import (
    decode_single_frame,
)
from ladon.semantic_candidate_protocol import (
    validate_application_rows as _validate_application_rows,
)
from ladon.semantic_candidate_protocol import (
    validate_worker_modules as _validate_worker_modules,
)
from ladon.semantic_candidate_protocol import (
    validate_worker_subject as _validate_worker_subject,
)
from ladon.semantic_local_context import (
    goal_with_local_context,
    validate_local_context,
    validate_observed_local_context,
)

SEMANTIC_PROTOCOL = "ladon-lean-semantic-v3/check-candidate"
SEMANTIC_BATCH_PROTOCOL = "ladon-lean-semantic-v3/check-candidates"
SEMANTIC_FRAME_PREFIX = "LADON_FRAME "
UNIVERSE_POLICY = "lean-level-mvar-succ-zero/v1"
FINGERPRINT_SCHEME = {"name": "lean-expr-structural", "version": "2"}
if (FINGERPRINT_SCHEME["name"], FINGERPRINT_SCHEME["version"]) not in SCHEMES:
    raise RuntimeError("semantic worker fingerprint scheme is not registered")
DEFAULT_HELPER = Path(
    str(resources.files("ladon").joinpath("lean", "ladon_semantic_candidate_helper.lean"))
)
MAX_GOAL_BYTES = 64 * 1024
MAX_IMPORTED_MODULES = 10_000
MAX_COMPILED_ENVIRONMENT_BYTES = 4 * 1024 * 1024 * 1024
MAX_EVIDENCE_FILE_BYTES = 512 * 1024 * 1024
TRUSTED_TARGET_LIMITATION = "Target modules may execute repository-controlled initializers; this observation is authority-scoped to trusted target code."
ProcessRunner = Callable[..., ProcessResult]


@dataclass(frozen=True)
class SemanticCandidateRequest:
    """One finite exact-candidate check in a caller-selected Lean repository."""

    repo_root: Path
    module: str
    goal: str
    candidate: str
    timeout_seconds: float = 120.0
    max_output_bytes: int = 8 * 1024 * 1024
    max_rss_bytes: int = 2 * 1024 * 1024 * 1024
    toolchain: LeanToolchainContext | None = None
    local_context: tuple[Mapping[str, str], ...] = ()
    execution_context_ref: str | None = None

    def __post_init__(self) -> None:
        _validate_request_identity(self.module, self.candidate)
        _validate_request_goal(self.goal)
        _validate_request_bounds(self.timeout_seconds, self.max_output_bytes, self.max_rss_bytes)
        validate_local_context(
            self.local_context,
            valid_name=_valid_local_name,
            validate_type=_validate_request_goal,
        )
        if self.toolchain is not None and self.execution_context_ref not in {
            None,
            self.toolchain.context_identity,
        }:
            raise ValueError("execution context reference must match the selected toolchain")


def _validate_request_identity(module: str, candidate: str) -> None:
    if not _valid_qualified_name(module):
        raise ValueError("semantic check module must be a qualified Lean name")
    if not _valid_qualified_name(candidate):
        raise ValueError("semantic check candidate must be a declaration name")


def _valid_qualified_name(value: str) -> bool:
    """Reject transport control characters; Lean owns name grammar.

    The request crosses an argv boundary, so punctuation is not a shell
    escape.  The helper parses the module/candidate with Lean's own term
    parser before looking up declarations; Python must not maintain a second,
    subtly different identifier grammar here.
    """
    return bool(value) and not any(char.isspace() or ord(char) < 32 for char in value)


def _valid_local_name(value: str) -> bool:
    return bool(value) and not any(
        char.isspace() or ord(char) < 32 or char in ":(){};" for char in value
    )


def _validate_request_goal(goal: str) -> None:
    if not goal:
        raise ValueError("semantic check requires a goal")
    forbidden = "\n" in goal or "\r" in goal or ":=" in goal
    if forbidden or len(goal.encode("utf-8")) > MAX_GOAL_BYTES:
        raise ValueError("semantic check goal must be one bounded Lean term")


def _validate_request_bounds(
    timeout_seconds: float, max_output_bytes: int, max_rss_bytes: int
) -> None:
    if (
        not math.isfinite(timeout_seconds)
        or min(timeout_seconds, max_output_bytes, max_rss_bytes) <= 0
    ):
        raise ValueError("semantic check bounds must be positive and finite")


@dataclass(frozen=True)
class SemanticCandidateCheck:
    """Terminal supervised result; artifacts exist only after Lean acceptance."""

    status: str
    artifacts: tuple[dict[str, Any], ...] = ()
    diagnostic: Mapping[str, Any] | None = None
    elapsed_seconds: float = 0.0
    peak_rss_bytes: int | None = None
    authority_selection: str = "not-assessed"
    analysis_completeness: str = "not-assessed"
    evidence_receipt: Mapping[str, Any] | None = None
    application_term: str | None = None
    discharged_hypotheses: tuple[Mapping[str, Any], ...] = ()
    caller_local_context: tuple[Mapping[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ladon-semantic-candidate-check-result-v1",
            "operation": "check-candidate",
            "status": self.status,
            "authoritySelection": self.authority_selection,
            "analysisCompleteness": self.analysis_completeness,
            "evidenceReceipt": dict(self.evidence_receipt) if self.evidence_receipt else None,
            "applicationTerm": self.application_term,
            "dischargedHypotheses": [dict(row) for row in self.discharged_hypotheses],
            "callerLocalContext": [dict(row) for row in self.caller_local_context],
            "artifacts": list(self.artifacts),
            "diagnostic": dict(self.diagnostic) if self.diagnostic else None,
            "resourceAccounting": {
                "elapsedSeconds": round(self.elapsed_seconds, 6),
                "peakRssBytes": self.peak_rss_bytes,
            },
            "limitations": [
                {
                    "id": "checker-observation-not-theorem-truth",
                    "message": "Acceptance records what this Lean process checked in this exact environment; Ladon does not promote it to an unqualified theorem-truth verdict.",
                }
            ],
        }


def check_semantic_candidate(
    request: SemanticCandidateRequest,
    *,
    helper_path: Path = DEFAULT_HELPER,
    runner: ProcessRunner = run_bounded_target_process,
    cancel_event: threading.Event | None = None,
) -> SemanticCandidateCheck:
    """Run the explicit Lean probe and publish artifacts only after validation."""

    probe_name = _probe_name(request)
    request_id = "req-" + secrets.token_hex(16)
    helper_identity = _digest_file(helper_path)
    source = _environment_source(request)
    with tempfile.TemporaryDirectory(prefix="ladon-semantic-check-") as directory:
        probe_path = Path(directory) / "Probe.lean"
        probe_path.write_text(source, encoding="utf-8")
        command = (
            (str(request.toolchain.lake_path), "env", str(request.toolchain.lean_path))
            if request.toolchain is not None
            else ("lake", "env", "lean")
        )
        try:
            process = _run_verified_candidate_process(
                request,
                runner,
                command
                + (
                    "--run",
                    str(helper_path),
                    f"Ladon.Semantic.{probe_name}",
                    str(probe_path),
                    goal_with_local_context(request.goal, request.local_context),
                    probe_name,
                    request.candidate,
                request_id,
                _execution_context_ref(request),
                ),
                helper_path,
                cancel_event,
                expected_helper_identity=helper_identity,
            )
        except LeanToolchainError as error:
            return _toolchain_identity_failure(request, error)
    if not process.succeeded:
        return _failed_check(process, request)
    try:
        payload = _parse_worker_payload(process.stdout, request, request_id)
        artifacts = _accepted_artifacts(
            request, helper_path, process, payload, helper_identity=helper_identity
        )
        validate_envelope_batch(list(artifacts))
    except (OSError, TypeError, ValueError) as error:
        return SemanticCandidateCheck(
            "invalid-worker-output",
            diagnostic={"code": "invalid-worker-output", "message": str(error)},
            elapsed_seconds=process.elapsed_seconds,
            peak_rss_bytes=process.peak_rss_bytes,
            evidence_receipt=_receipt_for_check(
                request, "failed", "invalid-worker-output", "invalid"
            ),
        )
    status = (
        "applicable-with-residuals"
        if artifacts[-1]["artifactKind"] == "proofir.attempt-log"
        else "accepted"
    )

    status_receipt = _receipt_for_check(
        request,
        "accepted",
        status,
        "partial" if status.endswith("residuals") else "complete",
        environment_ref=str(artifacts[0]["environmentRef"]),
        check_run_ref=str(artifacts[1]["payload"]["checkRunId"]),
        local_context=payload["localContext"],
    )
    return SemanticCandidateCheck(
        status,
        tuple(artifacts),
        elapsed_seconds=process.elapsed_seconds,
        peak_rss_bytes=process.peak_rss_bytes,
        authority_selection=(
            "explicit-pinned-application-check"
            if request.toolchain and request.toolchain.selection_mode == "explicit"
            else "ambient-selected-application-check"
        ),
        analysis_completeness=derive_analysis_completeness(
            operation_valid=True,
            required_populations=1,
            residuals=len(payload["residualPremises"]),
        ),
        evidence_receipt=status_receipt,
        application_term=payload["applicationTerm"],
        discharged_hypotheses=tuple(payload["dischargedHypotheses"]),
        caller_local_context=tuple(request.local_context),
    )


def _run_verified_candidate_process(
    request: SemanticCandidateRequest,
    runner: ProcessRunner,
    command: tuple[str, ...],
    helper_path: Path,
    cancel_event: threading.Event | None,
    *,
    expected_helper_identity: str | None = None,
) -> ProcessResult:
    helper_identity = expected_helper_identity or _digest_file(helper_path)
    if request.toolchain is not None:
        verify_toolchain_identities(request.toolchain)
    if _digest_file(helper_path) != helper_identity:
        raise LeanToolchainError("semantic helper identity changed during execution")
    process = runner(
        command,
        cwd=request.repo_root,
        env=(request.toolchain.environment if request.toolchain else None),
        timeout_seconds=request.timeout_seconds,
        max_output_bytes=request.max_output_bytes,
        max_rss_bytes=request.max_rss_bytes,
        cancel_event=cancel_event,
    )
    if request.toolchain is not None:
        verify_toolchain_identities(request.toolchain)
    if _digest_file(helper_path) != helper_identity:
        raise LeanToolchainError("semantic helper identity changed during execution")
    return process


def _toolchain_identity_failure(
    request: SemanticCandidateRequest, error: LeanToolchainError
) -> SemanticCandidateCheck:
    return SemanticCandidateCheck(
        "invalid-worker-output",
        diagnostic={"code": "toolchain-identity-changed", "message": str(error)},
        evidence_receipt=_receipt_for_check(request, "failed", "invalid-worker-output", "invalid"),
    )


def _receipt_for_check(
    request: SemanticCandidateRequest,
    outcome: str,
    status: str,
    completeness: str,
    environment_ref: str | None = None,
    check_run_ref: str | None = None,
    local_context: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    binding = "ambient-observed"
    environment_match = "unknown"
    if request.toolchain is not None:
        binding = (
            "explicit-pinned"
            if request.toolchain.selection_mode == "explicit"
            else "ambient-observed"
        )
        environment_match = (
            "exact"
            if outcome == "accepted" and environment_ref is not None
            else "unknown"
        )
    return build_evidence_receipt(
        subject={
            "module": request.module,
            "candidate": request.candidate,
            "goal": request.goal,
            "localContext": [
                {
                    "name": str(row.get("userName", row.get("name", ""))),
                    "type": str(row.get("typeDisplay", row.get("type", ""))),
                }
                for row in (local_context if local_context is not None else request.local_context)
            ],
        },
        execution_binding=binding,
        observation_state="live" if outcome in {"accepted", "rejected"} else "failed",
        operation_outcome=outcome,
        authority_basis=(
            "elaborator-check"
            if outcome == "accepted"
            else ("process-observation" if outcome == "rejected" else "not-assessed")
        ),
        analysis_completeness=completeness,
        environment_match=environment_match,
        environment_ref=environment_ref,
        check_run_ref=check_run_ref,
        limitations=(TRUSTED_TARGET_LIMITATION,)
        + (("Residual premises remain unverified.",) if status.endswith("residuals") else ()),
    )


def _probe_name(request: SemanticCandidateRequest) -> str:
    identity = _digest_text(
        canonical_bytes(
            {
                "module": request.module,
                "goal": request.goal,
                "candidate": request.candidate,
                "localContext": [dict(row) for row in request.local_context],
            }
        ).decode("utf-8")
    )
    return "ladonSemanticProbe_" + identity[7:23]


def _environment_source(request: SemanticCandidateRequest) -> str:
    """Provide only the requested module environment to the Lean helper."""
    return f"import {request.module}\nset_option autoImplicit false\n"


def _execution_context_ref(request: SemanticCandidateRequest) -> str:
    if request.toolchain is not None:
        return _digest_text(
            canonical_bytes(
                {
                    "baseContext": request.toolchain.context_identity,
                    "module": request.module,
                    "protocol": SEMANTIC_PROTOCOL,
                }
            ).decode()
        )
    return request.execution_context_ref or "unbound"


def _failed_check(
    process: ProcessResult, request: SemanticCandidateRequest
) -> SemanticCandidateCheck:
    if process.timed_out:
        code, status = "checker-timeout", "timeout"
    elif process.output_limited:
        code, status = "checker-output-limit", "output-limited"
    elif process.memory_limited:
        code, status = "checker-memory-limit", "memory-limited"
    elif any(
        marker in (process.stderr or process.stdout)
        for marker in ("invalid Lean name", "did not unify with the elaborated goal")
    ):
        code, status = "checker-rejected", "rejected"
    else:
        code, status = "checker-failed", "failed-checker"
    detail = (process.stderr or process.stdout).strip()
    return SemanticCandidateCheck(
        status,
        diagnostic={"code": code, "message": detail or code},
        elapsed_seconds=process.elapsed_seconds,
        peak_rss_bytes=process.peak_rss_bytes,
        evidence_receipt=_receipt_for_check(
            request,
            "rejected" if status == "rejected" else "failed",
            status,
            "not-assessed",
        ),
    )


def _parse_worker_payload(
    stdout: str, request: SemanticCandidateRequest, request_id: str
) -> dict[str, Any]:
    payload = _decode_single_frame(stdout)
    _validate_worker_frame(payload, request, request_id)
    _validate_worker_collections(payload)
    _validate_worker_identity(payload, request)
    _validate_application_rows(payload)
    _validate_discharged_hypotheses(payload)
    validate_observed_local_context(payload["localContext"], request.local_context)
    return payload


def _validate_worker_frame(
    payload: Mapping[str, Any], request: SemanticCandidateRequest, request_id: str
) -> None:
    if payload.get("protocol") != SEMANTIC_PROTOCOL:
        raise ValueError("Lean semantic helper emitted an unsupported protocol")
    required = {
        "frameVersion",
        "sequence",
        "terminal",
        "universePolicy",
        "leanVersion",
        "leanCommit",
        "requestId",
        "executionContextRef",
        "executablePath",
        "module",
        "probe",
        "candidate",
        "applicationTerm",
        "dischargedHypotheses",
        "importedModules",
        "substitutions",
        "residualPremises",
        "localContext",
    }
    if not required <= set(payload):
        raise ValueError("Lean semantic helper omitted required evidence fields")
    if payload["requestId"] != request_id:
        raise ValueError("Lean semantic helper returned a mismatched request ID")
    if payload["executionContextRef"] != _execution_context_ref(request):
        raise ValueError("Lean semantic helper returned a mismatched execution context")
    if payload["frameVersion"] != 1 or payload["sequence"] != 0 or payload["terminal"] is not True:
        raise ValueError("Lean semantic helper returned an invalid terminal frame")
    if payload["universePolicy"] != UNIVERSE_POLICY:
        raise ValueError("Lean semantic helper returned an unsupported universe policy")


def _validate_worker_collections(payload: Mapping[str, Any]) -> None:
    for field in (
        "substitutions",
        "dischargedHypotheses",
        "residualPremises",
        "localContext",
    ):
        if not isinstance(payload[field], list):
            raise TypeError(f"Lean semantic helper field {field} must be an array")
    if not isinstance(payload["applicationTerm"], str) or not payload["applicationTerm"]:
        raise ValueError("Lean semantic helper returned an invalid application term")


def _validate_discharged_hypotheses(payload: Mapping[str, Any]) -> None:
    local_ids = {str(row.get("localId")) for row in payload["localContext"]}
    for row in payload["dischargedHypotheses"]:
        if not isinstance(row, Mapping):
            raise TypeError("discharged hypothesis rows must be objects")
        if (
            not isinstance(row.get("premiseOrdinal"), int)
            or isinstance(row.get("premiseOrdinal"), bool)
            or row["premiseOrdinal"] < 0
            or not isinstance(row.get("premiseTypeDisplay"), str)
            or not row["premiseTypeDisplay"]
            or not isinstance(row.get("dischargedByLocalRef"), str)
            or row["dischargedByLocalRef"] not in local_ids
            or not isinstance(row.get("method"), str)
            or not row["method"]
        ):
            raise ValueError("discharged hypothesis refers to an unknown or malformed local")


def _decode_single_frame(stdout: str) -> dict[str, Any]:
    return decode_single_frame(stdout, SEMANTIC_FRAME_PREFIX)


def _validate_worker_identity(
    payload: Mapping[str, Any], request: SemanticCandidateRequest
) -> None:
    probe = payload.get("probe")
    candidate = payload.get("candidate")
    _validate_worker_subject(probe, "probe", _probe_name(request))
    requested_goal = " ".join(request.goal.split())
    observed_goal = " ".join(str(probe.get("typeDisplay", "")).split())
    if requested_goal != observed_goal and (
        requested_goal.isidentifier() or observed_goal.isidentifier()
    ):
        raise ValueError("Lean semantic helper returned a goal subject unrelated to the request")
    _validate_worker_subject(candidate, "candidate", request.candidate)
    expected_modules = {request.module, f"Ladon.Semantic.{_probe_name(request)}"}
    if payload.get("module") not in expected_modules:
        raise ValueError("Lean semantic helper returned a mismatched module")
    _validate_worker_modules(payload.get("importedModules"), request.module)
    if request.toolchain is not None:
        if (
            request.toolchain.selection_mode == "explicit"
            and Path(str(payload.get("executablePath"))).resolve() != request.toolchain.lean_path
        ):
            raise ValueError(
                "Lean semantic helper returned a foreign executable path: "
                f"{payload.get('executablePath')} != {request.toolchain.lean_path}"
            )
        expected = request.toolchain.pin_content.rsplit(":v", 1)[-1]
        versions = set(
            re.findall(
                r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?)(?![0-9])",
                str(payload.get("leanVersion")),
            )
        )
        if versions != {expected}:
            raise ValueError("Lean semantic helper returned an unbound Lean version")
        if request.toolchain.lean_commit is not None and str(payload.get("leanCommit", "")).lower() != request.toolchain.lean_commit:
            raise ValueError("Lean semantic helper returned an unbound Lean commit")


def _accepted_artifacts(
    request: SemanticCandidateRequest,
    helper_path: Path,
    process: ProcessResult,
    payload: Mapping[str, Any],
    *,
    helper_identity: str | None = None,
) -> tuple[dict[str, Any], ...]:
    environment = _environment_artifact(request.repo_root, payload, request.toolchain)
    env_ref = environment["environmentRef"]
    statement = _subject("statement", payload["probe"])
    statement["searchShape"] = {
        "declarationName": request.candidate,
        "role": "candidate-goal",
    }
    declaration = _subject("declaration", payload["candidate"])
    residuals = [_subject("statement", row) for row in payload["residualPremises"]]
    terms = [_term_subject(row) for row in payload["substitutions"]]
    context = _context_subject(env_ref, payload["localContext"])
    application = _application_subject(
        statement,
        declaration,
        residuals,
        payload["substitutions"],
        context,
        payload["dischargedHypotheses"],
        payload.get("applicationTerm"),
    )
    check = _check_artifact(
        request,
        env_ref,
        environment["artifactId"],
        statement,
        declaration,
        [*residuals, *terms],
        helper_path,
        process,
        payload,
        application,
        bool(residuals),
        helper_identity=helper_identity,
    )
    if residuals:
        attempt = _attempt_artifact(
            env_ref,
            statement,
            declaration,
            context,
            residuals,
            terms,
            payload["substitutions"],
            check,
            application,
            payload["dischargedHypotheses"],
        )
        return environment, check, attempt
    derivation = _derivation_artifact(
        env_ref,
        statement,
        declaration,
        context,
        terms,
        payload["substitutions"],
        check,
        application,
        payload["dischargedHypotheses"],
    )
    return environment, check, derivation


def _environment_artifact(
    repo_root: Path,
    payload: Mapping[str, Any],
    toolchain: LeanToolchainContext | None = None,
) -> dict[str, Any]:
    module_rows = payload["importedModules"]
    if len(module_rows) > MAX_IMPORTED_MODULES:
        raise ValueError("Lean semantic environment exceeds the module limit")
    compiled = []
    seen_modules: set[str] = set()
    total_bytes = 0
    for row in module_rows:
        module = str(row["module"])
        if module in seen_modules:
            raise ValueError("Lean semantic environment repeats a module identity")
        seen_modules.add(module)
        path = Path(str(row["oleanPath"])).resolve(strict=True)
        size = path.stat().st_size
        total_bytes += size
        if size > MAX_EVIDENCE_FILE_BYTES or total_bytes > MAX_COMPILED_ENVIRONMENT_BYTES:
            raise ValueError("Lean semantic environment exceeds its compiled-byte limit")
        compiled.append({"module": str(row["module"]), "digest": _digest_file(path)})
    compiled.sort(key=lambda row: (row["module"], row["digest"]))
    dependencies = []
    for name in (
        "lean-toolchain",
        "lake-manifest.json",
        "lakefile.lean",
        "lakefile.toml",
        "lakefile.json",
    ):
        path = repo_root / name
        if path.is_file():
            dependencies.append(
                {
                    "name": name,
                    "version": _digest_file(path),
                    "source": "repository-file",
                    "digest": _digest_file(path),
                }
            )
    manifest = {
        "prover": {"name": "Lean", "version": str(payload["leanVersion"])},
        "toolchain": {
            "name": "Lean",
            "version": str(payload["leanVersion"]),
            "commit": (
                str(payload["leanCommit"])
                if toolchain is None or toolchain.lean_commit is not None
                else "unknown"
            ),
        },
        "dependencies": dependencies,
        "compiledModules": compiled,
        "options": {
            "autoImplicit": False,
            "universeClosurePolicy": str(payload["universePolicy"]),
            "toolchainContext": (
                json.dumps(toolchain.to_dict(), sort_keys=True, separators=(",", ":"))
                if toolchain
                else "ambient-unbound"
            ),
        },
        "trust": {"axiomsAllowed": ["*"], "unsafeAllowed": False},
        "fingerprintScheme": dict(FINGERPRINT_SCHEME),
    }
    env_ref = _digest_bytes(canonical_bytes(manifest))
    return _envelope("proofir.environment", env_ref, [], manifest).to_dict()


def _subject(kind: str, row: Mapping[str, Any]) -> dict[str, Any]:
    structural = str(row["typeStructural"])
    if kind == "declaration":
        digest = _digest_bytes(
            canonical_bytes({"qualifiedName": str(row["name"]), "type": structural})
        )
        scheme = {"name": "lean-declaration-identity", "version": "1"}
    else:
        digest = _digest_text(structural)
        scheme = dict(FINGERPRINT_SCHEME)
    return {
        "kind": kind,
        "localId": f"{kind}:{digest}",
        "fingerprint": {"scheme": scheme, "digest": digest},
        "display": str(row["name"] if kind == "declaration" else row["typeDisplay"]),
    }


def _application_subject(
    statement: Mapping[str, Any],
    declaration: Mapping[str, Any],
    residuals: list[Mapping[str, Any]],
    substitutions: list[Mapping[str, Any]] | None = None,
    context: Mapping[str, Any] | None = None,
    discharged_hypotheses: list[Mapping[str, Any]] | None = None,
    application_term: str | None = None,
) -> dict[str, Any]:
    digest = _digest_bytes(
        canonical_bytes(
            {
                "statement": _identity_subject(statement),
                "declaration": _identity_subject(declaration),
                "residuals": [_identity_subject(row) for row in residuals],
                "substitutions": [
                    {
                        "variable": str(row["variable"]),
                        "termStructural": str(row["termStructural"]),
                    }
                    for row in (substitutions or [])
                ],
                "localContext": context["localId"] if context is not None else None,
                "dischargedHypotheses": [dict(row) for row in (discharged_hypotheses or [])],
                "applicationTerm": application_term,
            }
        )
    )
    return {
        "kind": "candidate-application",
        "localId": f"candidate-application:{digest}",
        "fingerprint": {
            "scheme": {"name": "lean-candidate-application", "version": "1"},
            "digest": digest,
        },
        "display": "candidate application",
    }


def _context_subject(
    environment_ref: str, local_context: list[Mapping[str, Any]] | None = None
) -> dict[str, Any]:
    locals_value = [dict(row) for row in (local_context or [])]
    identity_locals = [
        {
            key: row[key]
            for key in (
                "localId",
                "userName",
                "binderInfo",
                "typeStructural",
                "valueStructural",
                "dependencies",
                "origin",
            )
        }
        for row in locals_value
    ]
    digest = _digest_bytes(
        canonical_bytes({"environmentRef": environment_ref, "locals": identity_locals})
    )
    return {
        "kind": "local-context",
        "localId": f"local-context:{digest}",
        "fingerprint": {"scheme": {"name": "lean-local-context", "version": "1"}, "digest": digest},
        "display": "local context" if locals_value else "empty local context",
        "searchShape": {
            "environmentRef": environment_ref,
            "orderedLocals": locals_value,
            "origin": "goal-introduced" if locals_value else "empty",
        },
    }


def _identity_subject(subject: Mapping[str, Any]) -> dict[str, Any]:
    """Return only semantic identity fields; display text is presentation-only."""

    return {
        "kind": subject.get("kind"),
        "localId": subject.get("localId"),
        "fingerprint": subject.get("fingerprint"),
    }


def _term_subject(row: Mapping[str, Any]) -> dict[str, Any]:
    structural = str(row["termStructural"])
    digest = _digest_text(structural)
    return {
        "kind": "term",
        "localId": f"term:{digest}",
        "fingerprint": {"scheme": dict(FINGERPRINT_SCHEME), "digest": digest},
        "display": str(row["termDisplay"]),
    }


def _check_artifact(
    request: SemanticCandidateRequest,
    environment_ref: str,
    environment_artifact_id: str,
    statement: dict[str, Any],
    declaration: dict[str, Any],
    additional_subjects: list[dict[str, Any]],
    helper_path: Path,
    process: ProcessResult,
    payload: Mapping[str, Any],
    application: Mapping[str, Any],
    has_residuals: bool,
    *,
    helper_identity: str | None = None,
) -> dict[str, Any]:
    observation = {
        "universePolicy": str(payload["universePolicy"]),
        "command": list(process.command),
        "returnCode": process.returncode,
        "stdoutDigest": _digest_text(process.stdout),
        "stderrDigest": _digest_text(process.stderr),
        "helperDigest": helper_identity or _digest_file(helper_path),
        "executableDigest": _digest_file(Path(str(payload["executablePath"]))),
        "timeout": process.timed_out,
        "outputLimited": process.output_limited,
        "memoryLimited": process.memory_limited,
        "authoritySelection": (
            "explicit-pinned-application-check"
            if request.toolchain and request.toolchain.selection_mode == "explicit"
            else "ambient-selected-application-check"
        ),
        "analysisCompleteness": "partial" if has_residuals else "complete",
        "bounds": {
            "timeoutMs": max(1, int(request.timeout_seconds * 1000)),
            "maxOutputBytes": request.max_output_bytes,
            "maxRssBytes": request.max_rss_bytes,
        },
        "candidate": request.candidate,
        "applicationDigest": str(application["fingerprint"]["digest"]),
        "environmentRef": environment_ref,
    }
    check_id = "check:" + _digest_bytes(canonical_bytes(observation))[7:]
    observation["evidenceReceipt"] = _receipt_for_check(
        request,
        "accepted",
        "applicable-with-residuals" if has_residuals else "accepted",
        "partial" if has_residuals else "complete",
        environment_ref=environment_ref,
        check_run_ref=check_id,
        local_context=payload["localContext"],
    )
    check_subject = {
        "kind": "check-run",
        "localId": check_id,
        "display": "Lean exact-candidate check",
    }
    compact_statement = _compact(statement)
    compact_declaration = _compact(declaration)
    artifact = _envelope(
        "proofir.check-run",
        environment_ref,
        [
            statement,
            declaration,
            *_unique_subjects(additional_subjects),
            check_subject,
            application,
        ],
        {
            "checkRunId": check_id,
            "checker": {
                "name": "Lean",
                "version": str(payload["leanVersion"]),
                "implementationDigest": observation["helperDigest"],
                "executableDigest": observation["executableDigest"],
            },
            "operation": "exact-candidate-elaboration",
            "inputs": {
                "environmentRef": environment_ref,
                "subjectRefs": [
                    compact_statement,
                    compact_declaration,
                    *[_compact(row) for row in additional_subjects],
                    _compact(application),
                ],
                "artifactRefs": [environment_artifact_id],
            },
            "results": [
                {"subjectRef": _compact(application), "result": "accepted", "diagnostics": []},
                {
                    "subjectRef": compact_statement,
                    "result": "unchecked" if has_residuals else "accepted",
                    "diagnostics": [],
                },
            ],
            "outputs": {
                "stdoutDigest": observation["stdoutDigest"],
                "stderrDigest": observation["stderrDigest"],
            },
            "bounds": {
                "timeoutMs": max(1, int(request.timeout_seconds * 1000)),
                "maxOutputBytes": request.max_output_bytes,
            },
            "guarantee": {
                "scope": "route",
                "statement": "the named Lean elaborator accepted this candidate application shape; residual premises, when present, remain unproved",
                "authorityBasis": "elaborator-check",
            },
        },
        extensions={"ladon.process-observation/v1": observation},
    )
    return artifact.to_dict()


def _derivation_artifact(
    environment_ref: str,
    statement: dict[str, Any],
    declaration: dict[str, Any],
    context: dict[str, Any],
    terms: list[dict[str, Any]],
    substitution_rows: list[Mapping[str, Any]],
    check: Mapping[str, Any],
    application: Mapping[str, Any],
    discharged_hypotheses: list[Mapping[str, Any]],
) -> dict[str, Any]:
    step_digest = _digest_bytes(
        canonical_bytes(
            {
                "statement": _identity_subject(statement),
                "rule": _identity_subject(declaration),
                "context": context["localId"],
                "substitutions": [
                    {"variable": row["variable"], "termStructural": row["termStructural"]}
                    for row in substitution_rows
                ],
            }
        )
    )
    step = {"kind": "derivation-step", "localId": f"step:{step_digest}"}
    check_ref = {
        "artifactRef": check["artifactId"],
        "kind": "check-run",
        "localId": check["payload"]["checkRunId"],
    }
    artifact = _envelope(
        "proofir.derivation",
        environment_ref,
        [statement, declaration, context, application, *_unique_subjects(terms), step],
        {
            "derivationId": f"derivation:{step_digest}",
            "acyclic": True,
            "steps": [
                {
                    "stepRef": _compact(step),
                    "kind": "theorem-application",
                    "ruleRef": _compact(declaration),
                    "premiseRefs": [],
                    "conclusionRef": _compact(statement),
                    "substitutions": _substitution_refs(substitution_rows, terms),
                    "localContextRef": _compact(context),
                    "checkRunRef": check_ref,
                }
            ],
        },
        limitations=[
            {
                "id": "closed-exact-candidate-only",
                "message": "This derivation records a closed exact-candidate probe with no residual premises; substitutions and local context remain part of its identity.",
            }
        ],
        extensions={
            "ladon.premise-discharge/v1": {"rows": [dict(row) for row in discharged_hypotheses]}
        },
    )
    return artifact.to_dict()


def _attempt_artifact(
    environment_ref: str,
    statement: dict[str, Any],
    declaration: dict[str, Any],
    context: dict[str, Any],
    residuals: list[dict[str, Any]],
    terms: list[dict[str, Any]],
    substitution_rows: list[Mapping[str, Any]],
    check: Mapping[str, Any],
    application: Mapping[str, Any],
    discharged_hypotheses: list[Mapping[str, Any]],
) -> dict[str, Any]:
    identity = _digest_bytes(
        canonical_bytes(
            {
                "goal": _identity_subject(statement),
                "rule": _identity_subject(declaration),
                "residuals": [_identity_subject(row) for row in residuals],
                "context": context["localId"],
                "substitutions": [
                    {"variable": row["variable"], "termStructural": row["termStructural"]}
                    for row in substitution_rows
                ],
            }
        )
    )
    step = {"kind": "derivation-step", "localId": f"step:{identity}"}
    check_ref = {
        "artifactRef": check["artifactId"],
        "kind": "check-run",
        "localId": check["payload"]["checkRunId"],
    }
    residual_refs = [_compact(row) for row in residuals]
    return _envelope(
        "proofir.attempt-log",
        environment_ref,
        [
            statement,
            declaration,
            context,
            *_unique_subjects(residuals),
            application,
            *_unique_subjects(terms),
            step,
        ],
        {
            "attemptLogId": f"attempt-log:{identity}",
            "goalRef": _compact(statement),
            "attempts": [
                {
                    "attemptId": f"attempt:{identity}",
                    "stepRef": _compact(step),
                    "ruleRef": _compact(declaration),
                    "premiseRefs": residual_refs,
                    "conclusionRef": _compact(statement),
                    "substitutions": _substitution_refs(substitution_rows, terms),
                    "checkRunRef": check_ref,
                    "outcome": "accepted",
                    "diagnostics": [],
                }
            ],
            "summary": {
                "outcome": "incomplete",
                "residualPremiseRefs": residual_refs,
            },
        },
        limitations=[
            {
                "id": "application-has-residual-premises",
                "message": "Lean accepted the candidate application shape, but the residual premises are not discharged and this attempt is not a proof.",
            }
        ],
        extensions={
            "ladon.lean-attempt-context/v1": {
                "attemptId": f"attempt:{identity}",
                "localContextRef": _compact(context),
            },
            "ladon.premise-discharge/v1": {"rows": [dict(row) for row in discharged_hypotheses]},
        },
    ).to_dict()


def _substitution_refs(
    rows: list[Mapping[str, Any]], terms: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if len(rows) != len(terms):
        raise ValueError("worker substitution descriptors are inconsistent")
    return [
        {"variable": str(row["variable"]), "termRef": _compact(term)}
        for row, term in zip(rows, terms)
    ]


def _envelope(
    kind: str,
    environment_ref: str,
    subjects: list[dict[str, Any]],
    payload: dict[str, Any],
    *,
    limitations: list[dict[str, str]] | None = None,
    extensions: dict[str, Any] | None = None,
) -> ProofIRV3Artifact:
    observed = len(subjects)
    return make_envelope(
        artifact_kind=kind,
        producer={
            "name": "ladon-semantic-candidate-worker",
            "version": "1",
            "implementation": "python+lean",
            "buildDigest": _digest_file(Path(__file__)),
        },
        environment_ref=environment_ref,
        subject_refs=subjects,
        coverage={
            "status": "complete",
            "population": {"kind": "worker-result-subjects", "selector": {}},
            "universeKnown": True,
            "expected": observed,
            "discovered": observed,
            "decoded": observed,
            "valid": observed,
            "projected": observed,
            "queryMatched": observed,
            "omitted": [],
            "bounds": {"maxCandidates": 1},
        },
        payload=payload,
        limitations=limitations or [],
        extensions=extensions or {},
    )


def _compact(subject: Mapping[str, Any]) -> dict[str, str]:
    return {"kind": str(subject["kind"]), "localId": str(subject["localId"])}


def _unique_subjects(subjects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique = []
    for subject in subjects:
        key = (str(subject["kind"]), str(subject["localId"]))
        if key not in seen:
            seen.add(key)
            unique.append(subject)
    return unique


def _digest_text(value: str) -> str:
    return _digest_bytes(value.encode("utf-8"))


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _digest_file(path: Path) -> str:
    if path.stat().st_size > MAX_EVIDENCE_FILE_BYTES:
        raise ValueError(f"evidence file exceeds byte limit: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


__all__ = [
    "DEFAULT_HELPER",
    "SEMANTIC_BATCH_PROTOCOL",
    "SemanticCandidateCheck",
    "SemanticCandidateRequest",
    "check_semantic_candidate",
]
